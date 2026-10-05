package de.piu.kyc;

import java.util.Map;

import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;

import org.eclipse.microprofile.rest.client.inject.RegisterRestClient;

/** REST-Client für den Laya-Dienst (laya_kyc/laya_service.py). URL: quarkus.rest-client.laya.url */
@RegisterRestClient(configKey = "laya")
@Consumes(MediaType.APPLICATION_JSON)
@Produces(MediaType.APPLICATION_JSON)
public interface LayaClient {

    @POST
    @Path("/assessment")
    LlmResult assess(Map<String, Object> request);

    @GET
    @Path("/health")
    Map<String, Object> health();
}
