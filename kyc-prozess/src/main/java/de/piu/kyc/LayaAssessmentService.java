package de.piu.kyc;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

import org.eclipse.microprofile.rest.client.inject.RestClient;
import org.jboss.logging.Logger;

/**
 * Implementierung des BPMN-Service-Tasks "Prüfung mit LLM".
 *
 * <p>Ergänzt den Antrag um das im Prozess berechnete Regelergebnis, so wie das Modell es im
 * Training gesehen hat, und ruft den Laya-Dienst auf. Ein vom Aufrufer mitgeliefertes
 * {@code regelpruefung}-Feld wird überschrieben. Technische Fehler führen nicht zum Abbruch,
 * sondern zur Empfehlung einer manuellen Prüfung.
 */
@ApplicationScoped
public class LayaAssessmentService {

    private static final Logger LOG = Logger.getLogger(LayaAssessmentService.class);

    @Inject
    @RestClient
    LayaClient laya;

    /**
     * Regeln, die Laya aus dem Training kennt. Spätere Regeln (z. B. R4 USA-Bezug) setzt allein der
     * Prozess durch; sie erzwingen die manuelle Prüfung unabhängig vom Modell und würden das Modell
     * nur mit einer nie gesehenen Eingabe konfrontieren.
     */
    static final Set<String> MODEL_RULES = Set.of("R1", "R2", "R3");

    public LlmResult assess(Map<String, Object> application, List<String> triggeredRules) {
        List<String> rules = triggeredRules == null ? List.of()
                : triggeredRules.stream().filter(MODEL_RULES::contains).toList();
        // Feldnamen gehören zum Datensatzschema, mit dem Laya trainiert wurde.
        Map<String, Object> input = new LinkedHashMap<>(application);
        input.put("regelpruefung", Map.of(
                "ergebnis", rules.isEmpty() ? "Gruen" : "Pruefbedarf",
                "ausgeloeste_regeln", rules));
        try {
            LlmResult result = laya.assess(Map.of("application", input));
            if (result == null || result.getDecision() == null) {
                return LlmResult.error("Leere Antwort des Laya-Dienstes");
            }
            LOG.infof("Laya: %s %s", result.getDecision(), result.getProbabilities());
            return result;
        } catch (RuntimeException e) {
            LOG.warnf("Laya-Dienst nicht nutzbar, Fall geht zur manuellen Prüfung: %s", e.getMessage());
            return LlmResult.error(e.getClass().getSimpleName() + ": " + e.getMessage());
        }
    }
}
