def get_silence_time(call_data):
    silence_time_data = []
    user_idx = 0
    agent_idx = 0
    for idx,i in enumerate(call_data["transcript_object"]):
        if i['role'] == "user":
            user_idx = idx
            if len(call_data["transcript_object"]) == user_idx + 1:
                break
            else:
                if call_data["transcript_object"][user_idx+1]['role'] == "agent":
                    user_last_word_endtime = i["words"][-1]["end"]
                    agent_first_word_starttime = call_data["transcript_object"][user_idx+1]["words"][0]["start"]
                    silence_time = agent_first_word_starttime - user_last_word_endtime
                    query = call_data["transcript_object"][user_idx]["content"]
                    silence_time_data.append({
                        "start": user_last_word_endtime,
                        "end": agent_first_word_starttime,
                        "duration": silence_time,
                        "query": query
                    })

    return silence_time_data