package de.piu.kyc.dashboard;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;

import jakarta.inject.Inject;
import jakarta.ws.rs.DELETE;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.NotFoundException;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;

import org.eclipse.microprofile.rest.client.inject.RestClient;

import de.piu.kyc.LayaClient;

/** Daten für Webinterface und Dashboard. */
@Path("/api/dashboard")
@Produces(MediaType.APPLICATION_JSON)
public class DashboardResource {

    @Inject
    InstanceHistoryStore store;

    @Inject
    @RestClient
    LayaClient laya;

    /** Erreichbarkeit des Laya-Dienstes für die Statusanzeige. */
    @GET
    @Path("/status")
    public Map<String, Object> status() {
        try {
            return Map.of("laya", laya.health());
        } catch (RuntimeException e) {
            return Map.of("laya", Map.of("status", "unreachable", "error", String.valueOf(e.getMessage())));
        }
    }

    @GET
    @Path("/instances")
    public List<Map<String, Object>> instances() {
        return store.all().stream().map(InstanceHistory::summary).toList();
    }

    @GET
    @Path("/instances/{id}")
    public InstanceHistory instance(@PathParam("id") String id) {
        return store.find(id).orElseThrow(() -> new NotFoundException("Unbekannte Instanz " + id));
    }

    @DELETE
    @Path("/instances")
    public void clear() {
        store.clear();
    }

    /** Das ausgeführte BPMN, für die Darstellung mit bpmn-js. */
    @GET
    @Path("/process.bpmn")
    @Produces(MediaType.APPLICATION_XML)
    public String processDefinition() throws IOException {
        return classpathResource("/KYC_Pruefprozess.bpmn");
    }

    private static String classpathResource(String path) throws IOException {
        try (InputStream in = DashboardResource.class.getResourceAsStream(path)) {
            if (in == null) {
                throw new NotFoundException(path);
            }
            return new String(in.readAllBytes(), StandardCharsets.UTF_8);
        }
    }
}
