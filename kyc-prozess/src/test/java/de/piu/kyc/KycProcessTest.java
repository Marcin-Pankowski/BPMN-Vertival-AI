package de.piu.kyc;

import static io.restassured.RestAssured.given;
import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.Matchers.contains;
import static org.hamcrest.Matchers.empty;
import static org.hamcrest.Matchers.equalTo;
import static org.hamcrest.Matchers.hasSize;
import static org.hamcrest.Matchers.nullValue;
import static org.hamcrest.Matchers.startsWith;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.argThat;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.eclipse.microprofile.rest.client.inject.RestClient;
import org.junit.jupiter.api.Test;

import io.quarkus.test.InjectMock;
import io.quarkus.test.junit.QuarkusTest;
import io.restassured.http.ContentType;
import io.restassured.response.ValidatableResponse;

@QuarkusTest
class KycProcessTest {

    private static final String REVIEWER = "user=reviewer&group=kyc-reviewers";

    @InjectMock
    @RestClient
    LayaClient laya;

    @Test
    void greenRulesAndNoLlmFindingAreApprovedAutomatically() {
        layaReturns("keine_manuelle_pruefung");
        String id = start(application("Ja", "Nein", "kein_treffer"))
                .body("rule_result", equalTo("green"))
                .body("triggered_rules", empty())
                .body("llm_result.decision", equalTo("keine_manuelle_pruefung"))
                .extract().path("id");
        assertCompleted(id);
        given().get("/api/dashboard/instances/" + id).then().statusCode(200)
                .body("status", equalTo("completed"))
                .body("outcome", equalTo("approved"))
                .body("steps.nodeId", contains("Start_KYC", "Task_Rules", "Gateway_Rules", "Task_LLM",
                        "Gateway_LLM", "Gateway_Join_Approve", "End_Approve"));
    }

    @Test
    void ruleTriggerForcesManualReviewDespiteLlmRelease() {
        layaReturns("keine_manuelle_pruefung");
        String id = start(application("Ja", "Ja", "kein_treffer"))
                .body("rule_result", equalTo("review"))
                .body("triggered_rules", contains("R2"))
                .extract().path("id");
        given().get("/api/dashboard/instances/" + id).then()
                .body("status", equalTo("active"))
                .body("steps[-1].nodeId", equalTo("Task_Manual"));
        decide(openTask(id), "approve");
        assertCompleted(id);
    }

    @Test
    void llmFindingLeadsToManualReviewAndRejection() {
        layaReturns("manuelle_pruefung");
        String id = start(application("Ja", "Nein", "kein_treffer")).body("rule_result", equalTo("green")).extract().path("id");
        decide(openTask(id), "reject");
        assertCompleted(id);
        given().get("/api/dashboard/instances/" + id).then()
                .body("outcome", equalTo("rejected"))
                .body("manualDecision", equalTo("reject"));
    }

    @Test
    void confirmedSanctionsHitIsRejectedByRulesWithoutLaya() {
        String id = start(application("Ja", "Nein", "bestaetigter_treffer"))
                .body("rule_result", equalTo("reject"))
                .body("triggered_rules", contains("R5"))
                .body("llm_result", nullValue())
                .extract().path("id");
        assertCompleted(id);
        verify(laya, never()).assess(any());
        given().get("/api/dashboard/instances/" + id).then()
                .body("outcome", equalTo("rejected"))
                .body("steps.nodeId", contains("Start_KYC", "Task_Rules", "Gateway_Rules", "Gateway_Join_Reject", "End_Reject"));
    }

    @Test
    void unavailableLayaServiceLeadsToManualReview() {
        when(laya.assess(any())).thenThrow(new RuntimeException("Connection refused"));
        String id = start(application("Ja", "Nein", "kein_treffer"))
                .body("llm_result.decision", equalTo(LlmResult.DECISION_ERROR))
                .body("llm_result.manual_review_recommended", equalTo(true))
                .body("llm_result.error", startsWith("RuntimeException"))
                .extract().path("id");
        openTask(id);
    }

    @Test
    void invalidDecisionCreatesNewTask() {
        layaReturns("unklar");
        String id = start(application("Nein", "Nein", "moeglicher_treffer_ungeklaert"))
                .body("triggered_rules", contains("R1", "R3"))
                .extract().path("id");
        decide(openTask(id), "vielleicht");
        String second = openTask(id);
        given().contentType(ContentType.JSON).body(Map.of("transitionId", "skip"))
                .post("/usertasks/instance/" + second + "/transition?" + REVIEWER).then().statusCode(200);
        decide(openTask(id), "approve");
        assertCompleted(id);
    }

    @Test
    void usNexusForcesManualReviewAndIsNotPassedToLaya() {
        layaReturns("keine_manuelle_pruefung");
        Map<String, Object> app = application("Ja", "Nein", "kein_treffer");
        app.put("steuerangaben", Map.of("us_steuerpflicht_laut_selbstauskunft", "Ja",
                "fatca_us_person_laut_selbstauskunft", "Ja", "steuerliche_ansaessigkeit_laut_selbstauskunft", List.of("DE", "US")));
        String id = start(app)
                .body("rule_result", equalTo("review"))
                .body("triggered_rules", contains("R4"))
                .extract().path("id");
        openTask(id);
        verify(laya).assess(argThat(request -> {
            Map<?, ?> input = (Map<?, ?>) request.get("application");
            Map<?, ?> ruleCheck = (Map<?, ?>) input.get("regelpruefung");
            return "Gruen".equals(ruleCheck.get("ergebnis")) && ((List<?>) ruleCheck.get("ausgeloeste_regeln")).isEmpty();
        }));
    }

    @Test
    void usNexusDetectedFromEachIndicator() {
        List<Map<String, Object>> indicators = List.of(
                Map.of("steuerangaben", Map.of("fatca_us_person_laut_selbstauskunft", "Ja")),
                Map.of("steuerangaben", Map.of("steuerliche_ansaessigkeit_laut_selbstauskunft", List.of("DE", "US"))),
                Map.of("kunde", Map.of("staatsangehoerigkeiten", List.of("DE", "US"))),
                Map.of("kunde", Map.of("adresse", Map.of("land", "US"))),
                Map.of("kunde", Map.of("auslandsadressen", List.of(Map.of("land", "CH"), Map.of("land", "US")))));
        for (Map<String, Object> indicator : indicators) {
            given().contentType(ContentType.JSON).body(Map.of("Application", indicator))
                    .post("/KYC_RuleCheck")
                    .then().statusCode(200)
                    .body("TriggeredRules", contains("R4"));
        }
        Map<String, Object> noNexus = Map.of(
                "kunde", Map.of("staatsangehoerigkeiten", List.of("DE"), "adresse", Map.of("land", "DE"),
                        "auslandsadressen", List.of(Map.of("land", "CH"))),
                "steuerangaben", Map.of("us_steuerpflicht_laut_selbstauskunft", "Nein",
                        "fatca_us_person_laut_selbstauskunft", "Nein", "steuerliche_ansaessigkeit_laut_selbstauskunft", List.of("DE", "CH")));
        given().contentType(ContentType.JSON).body(Map.of("Application", noNexus))
                .post("/KYC_RuleCheck")
                .then().statusCode(200)
                .body("TriggeredRules", empty())
                .body("RuleResult", equalTo("green"));
    }

    @Test
    void rulesAsDmnDecision() {
        given().contentType(ContentType.JSON)
                .body(Map.of("Application", application("Nein", "Ja", "moeglicher_treffer_ungeklaert")))
                .post("/KYC_RuleCheck")
                .then().statusCode(200)
                .body("TriggeredRules", contains("R1", "R2", "R3"))
                .body("RuleResult", equalTo("review"));
    }

    private void layaReturns(String decision) {
        LlmResult result = new LlmResult();
        result.setDecision(decision);
        result.setManualReviewRecommended(!"keine_manuelle_pruefung".equals(decision));
        result.setProbabilities(Map.of(decision, 1.0));
        when(laya.assess(any())).thenReturn(result);
    }

    /** Minimaler Antrag; Feldnamen folgen dem Datensatzschema. */
    private static Map<String, Object> application(String beneficialOwner, String pep, String screening) {
        Map<String, Object> app = new HashMap<>();
        app.put("kunde", Map.of("vorname", "Test", "nachname", "Fall", "ist_selbst_wirtschaftlich_berechtigt", beneficialOwner));
        app.put("screening", Map.of("pep", pep, "sanktionsscreening_status", screening));
        app.put("kontoantrag", Map.of("kontotyp", "Privatkonto"));
        return app;
    }

    private static ValidatableResponse start(Map<String, Object> application) {
        return given().contentType(ContentType.JSON).body(Map.of("application", application))
                .post("/kyc_review").then().statusCode(201);
    }

    private static String openTask(String processInstanceId) {
        List<String> ids = given().get("/usertasks/instance?" + REVIEWER).then().statusCode(200)
                .extract().path("findAll { it.processInfo.processInstanceId == '" + processInstanceId
                        + "' && it.status.name == 'Ready' }.id");
        assertThat(ids, hasSize(1));
        return ids.get(0);
    }

    private static void decide(String taskId, String decision) {
        String url = "/usertasks/instance/" + taskId + "/transition?" + REVIEWER;
        given().contentType(ContentType.JSON).body(Map.of("transitionId", "claim")).post(url).then().statusCode(200);
        given().contentType(ContentType.JSON)
                .body(Map.of("transitionId", "complete", "data", Map.of("decision", decision, "comment", "Test")))
                .post(url).then().statusCode(200);
    }

    private static void assertCompleted(String processInstanceId) {
        given().get("/kyc_review/" + processInstanceId).then().statusCode(404);
    }
}
