def segment_event(df, condition, event_type):

    events = []

    active = False
    start_time = None

    for _, row in df.iterrows():

        cond = condition(row)

        if cond and not active:

            active = True
            start_time = row["Timestamp"]

        elif not cond and active:

            duration = (row["Timestamp"] - start_time).total_seconds()

            events.append({
                "type": event_type,
                "timestamp": start_time.isoformat(),
                "duration": int(duration)
            })

            active = False

    return events