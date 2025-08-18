def get_silence_time(call_data):

    total_silence_time = 0
    individual_silence_time = []
    for idx,i in enumerate(call_data["transcript_object"]):
        if i['role'] == "user":
            last_word_endtime = i["words"][-1]["end"]
            for j in call_data["transcript_object"][idx:]:
                if j['role'] == "agent":
                    first_word_starttime = j["words"][0]["start"]
                    silence_time = first_word_starttime - last_word_endtime
                    individual_silence_time.append(silence_time)
                    total_silence_time+=silence_time
                    break
                
    return total_silence_time, individual_silence_time