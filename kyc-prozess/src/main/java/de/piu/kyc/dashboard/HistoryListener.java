package de.piu.kyc.dashboard;

import java.time.Instant;
import java.util.List;
import java.util.Map;

import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

import org.kie.api.event.process.ProcessCompletedEvent;
import org.kie.api.event.process.ProcessEvent;
import org.kie.api.event.process.ProcessNodeTriggeredEvent;
import org.kie.api.event.process.ProcessStartedEvent;
import org.kie.api.event.process.ProcessVariableChangedEvent;
import org.kie.api.runtime.process.NodeInstance;
import org.kie.api.runtime.process.ProcessInstance;
import org.kie.kogito.internal.process.event.DefaultKogitoProcessEventListener;
import org.kie.kogito.internal.process.runtime.KogitoNodeInstance;
import org.kie.kogito.internal.process.runtime.KogitoProcessInstance;

import de.piu.kyc.LlmResult;

/** Schreibt Knoten, Variablen und Ende jeder KYC-Prozessinstanz in den {@link InstanceHistoryStore}. */
@ApplicationScoped
public class HistoryListener extends DefaultKogitoProcessEventListener {

    @Inject
    InstanceHistoryStore store;

    @Override
    public void beforeProcessStarted(ProcessStartedEvent event) {
        store.update(instanceId(event), h -> h.start = eventTime(event));
    }

    @Override
    public void beforeNodeTriggered(ProcessNodeTriggeredEvent event) {
        NodeInstance nodeInstance = event.getNodeInstance();
        String nodeId = nodeId(nodeInstance);
        if (nodeId == null) {
            return;
        }
        Instant now = eventTime(event);
        store.update(instanceId(event), h -> {
            // Der Prozess ist sequenziell: Wird ein Knoten betreten, ist der vorige verlassen.
            // (afterNodeLeft feuert in jBPM erst, wenn der gesamte nachfolgende Ablauf zurückkehrt.)
            h.steps.replaceAll(s -> s.left() == null ? s.leave(now) : s);
            h.steps.add(new InstanceHistory.Step(nodeId, nodeInstance.getNodeName(), now, null));
            if (nodeId.startsWith("End_")) {
                h.outcome = "End_Approve".equals(nodeId) ? "approved" : "rejected";
            }
        });
    }

    @Override
    @SuppressWarnings("unchecked")
    public void afterVariableChanged(ProcessVariableChangedEvent event) {
        Object value = event.getNewValue();
        store.update(instanceId(event), h -> {
            switch (event.getVariableId()) {
                case "application" -> {
                    h.application = (Map<String, Object>) value;
                    h.customer = customerName(h.application);
                }
                case "rule_result" -> h.ruleResult = (String) value;
                case "triggered_rules" -> h.triggeredRules = (List<String>) value;
                case "llm_result" -> h.llmResult = (LlmResult) value;
                case "manual_decision" -> h.manualDecision = (String) value;
                case "manual_comment" -> h.manualComment = (String) value;
                default -> {
                }
            }
        });
    }

    @Override
    public void afterProcessCompleted(ProcessCompletedEvent event) {
        int state = event.getProcessInstance().getState();
        store.update(instanceId(event), h -> {
            h.end = eventTime(event);
            h.steps.replaceAll(s -> s.left() == null ? s.leave(h.end) : s);
            h.status = switch (state) {
                case ProcessInstance.STATE_COMPLETED -> "completed";
                case ProcessInstance.STATE_ABORTED -> "aborted";
                case KogitoProcessInstance.STATE_ERROR -> "error";
                default -> "state " + state;
            };
        });
    }

    private static String instanceId(ProcessEvent event) {
        return ((KogitoProcessInstance) event.getProcessInstance()).getStringId();
    }

    private static Instant eventTime(ProcessEvent event) {
        return event.getEventDate() == null ? Instant.now() : event.getEventDate().toInstant();
    }

    /** BPMN-Element-ID wie im Diagramm (z. B. Task_Rules). */
    private static String nodeId(NodeInstance nodeInstance) {
        Object uniqueId = nodeInstance.getNode() == null ? null : nodeInstance.getNode().getMetaData().get("UniqueId");
        if (uniqueId != null) {
            return uniqueId.toString();
        }
        return nodeInstance instanceof KogitoNodeInstance kni ? kni.getNodeDefinitionId() : null;
    }

    /** Die Antragsfelder folgen dem Datensatzschema (deutsch). */
    @SuppressWarnings("unchecked")
    private static String customerName(Map<String, Object> application) {
        if (application == null || !(application.get("kunde") instanceof Map<?, ?> raw)) {
            return null;
        }
        Map<String, Object> person = (Map<String, Object>) raw;
        return (person.getOrDefault("vorname", "") + " " + person.getOrDefault("nachname", "")).trim();
    }
}
