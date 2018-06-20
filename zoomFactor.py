# Algorithmically Determined
def zoomFactor(self, event_list, lat_top):
        lat_list = list()
        
        for i in range(len(event_list)):
                lat_list.append(event_list[i][2])
                
        diff = 0.0
        for lat in lat_list:
                diff += (float(lat_top) - float(lat))

        if(len(lat_list) > 0):
                avg_diff = diff / len(lat_list)
        else:
            return 0

        if(avg_diff >= 0 and avg_diff <= 0.045):
            return 1
        elif(avg_diff > 0.045 and avg_diff <= 0.085):
            return 0.92
        elif(avg_diff > 0.085 and avg_diff <= 0.125):
            return 0.84
        elif(avg_diff > 0.125 and avg_diff <= 0.165):
            return 0.76
        elif(avg_diff > 0.205 and avg_diff <= 0.245):
            return 0.68
        elif(avg_diff > 0.245 and avg_diff <= 0.285):
            return 0.6
        elif(avg_diff > 0.285 and avg_diff <= 0.325):
            return 0.52
        elif(avg_diff > 0.325 and avg_diff <= 0.365):
            return 0.44
        elif(avg_diff > 0.365 and avg_diff <= 0.405):
            return 0.36
        elif(avg_diff > 0.405 and avg_diff <= 0.445):
            return 0.28
        elif(avg_diff > 0.445 and avg_diff <= 0.485):
            return 0.2
        elif(avg_diff > 0.485 and avg_diff <= 0.525):
            return 0.12
        elif(avg_diff > 0.525):
            return 0.06
