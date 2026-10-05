package de.piu.kyc.dashboard;

import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Consumer;

import jakarta.enterprise.context.ApplicationScoped;

/**
 * Speicher für die Instanzverläufe. Bewusst nur im Arbeitsspeicher, wie die Prozessinstanzen selbst;
 * die ältesten Einträge fallen nach {@link #MAX_ENTRIES} Instanzen heraus.
 */
@ApplicationScoped
public class InstanceHistoryStore {

    static final int MAX_ENTRIES = 1000;

    private final Map<String, InstanceHistory> histories = new ConcurrentHashMap<>();

    void update(String id, Consumer<InstanceHistory> change) {
        InstanceHistory history = histories.computeIfAbsent(id, key -> {
            InstanceHistory created = new InstanceHistory();
            created.id = key;
            return created;
        });
        synchronized (history) {
            change.accept(history);
        }
        if (histories.size() > MAX_ENTRIES) {
            all().stream().skip(MAX_ENTRIES).forEach(old -> histories.remove(old.id));
        }
    }

    /** Neueste zuerst. */
    public List<InstanceHistory> all() {
        return histories.values().stream()
                .sorted(Comparator.comparing((InstanceHistory h) -> h.start,
                        Comparator.nullsLast(Comparator.naturalOrder())).reversed())
                .toList();
    }

    public Optional<InstanceHistory> find(String id) {
        return Optional.ofNullable(histories.get(id));
    }

    public void clear() {
        histories.clear();
    }
}
