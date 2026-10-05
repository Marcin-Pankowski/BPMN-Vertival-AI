package de.piu.kyc;

import java.io.Serializable;
import java.util.Map;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;

/**
 * Ergebnis des BPMN-Tasks "Prüfung mit LLM" (JSON in snake_case wie die Laya-API).
 *
 * <p>{@code decision} ist {@code keine_manuelle_pruefung}, {@code manuelle_pruefung},
 * {@code unklar} oder {@code fehler}. Bei {@code fehler} (Dienst nicht erreichbar, ungültige
 * Antwort) wird manuelle Prüfung empfohlen.
 */
@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public class LlmResult implements Serializable {

    private static final long serialVersionUID = 1L;

    public static final String DECISION_ERROR = "fehler";

    private String decision;
    private boolean manualReviewRecommended;
    private Map<String, Double> probabilities;
    private String model;
    private String error;

    public LlmResult() {
    }

    public static LlmResult error(String message) {
        LlmResult result = new LlmResult();
        result.decision = DECISION_ERROR;
        result.manualReviewRecommended = true;
        result.error = message;
        return result;
    }

    public String getDecision() {
        return decision;
    }

    public void setDecision(String decision) {
        this.decision = decision;
    }

    public boolean isManualReviewRecommended() {
        return manualReviewRecommended;
    }

    public void setManualReviewRecommended(boolean manualReviewRecommended) {
        this.manualReviewRecommended = manualReviewRecommended;
    }

    public Map<String, Double> getProbabilities() {
        return probabilities;
    }

    public void setProbabilities(Map<String, Double> probabilities) {
        this.probabilities = probabilities;
    }

    public String getModel() {
        return model;
    }

    public void setModel(String model) {
        this.model = model;
    }

    public String getError() {
        return error;
    }

    public void setError(String error) {
        this.error = error;
    }

    @Override
    public String toString() {
        return "LlmResult[" + decision + ", manualReview=" + manualReviewRecommended
                + (error != null ? ", error=" + error : "") + "]";
    }
}
