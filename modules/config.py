def build_chainmap_trace_options():
    return {
        "tracer": "callTracer",
        "tracerConfig": {
            "withLog": True,
        },
    }
