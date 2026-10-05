package de.piu.kyc.dashboard;

import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import de.piu.kyc.LlmResult;

/** Verlauf einer Prozessinstanz für das Dashboard; bleibt nach Abschluss im Speicher. */
public class InstanceHistory {

    public static final String STATUS_ACTIVE = "active";

    /** Ein durchlaufener BPMN-Knoten. {@code left == null} heißt: Instanz wartet hier. */
    public record Step(String nodeId, String name, Instant entered, Instant left) {
        Step leave(Instant time) {
            return new Step(nodeId, name, entered, time);
        }
    }

    public String id;
    /** active, completed, aborted oder error */
    public String status = STATUS_ACTIVE;
    public Instant start;
    public Instant end;
    /** approved oder rejected, sobald ein End-Event erreicht ist */
    public String outcome;
    public String customer;
    public Map<String, Object> application;
    public String ruleResult;
    public List<String> triggeredRules;
    public LlmResult llmResult;
    public String manualDecision;
    public String manualComment;
    public final List<Step> steps = new ArrayList<>();

    /** Kurzfassung für die Instanzliste, ohne Antrag und Schritte. */
    public Map<String, Object> summary() {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", id);
        m.put("status", status);
        m.put("start", start);
        m.put("end", end);
        m.put("outcome", outcome);
        m.put("customer", customer);
        m.put("ruleResult", ruleResult);
        m.put("triggeredRules", triggeredRules);
        m.put("llmDecision", llmResult == null ? null : llmResult.getDecision());
        m.put("manualDecision", manualDecision);
        m.put("waitingAt", STATUS_ACTIVE.equals(status)
                ? steps.stream().filter(s -> s.left() == null).map(Step::name).findFirst().orElse(null)
                : null);
        return m;
    }
}
