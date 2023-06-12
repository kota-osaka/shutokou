import pprint

#from shutokou_share import euler_graphs, xlsx2vert_edges_dict
from shutokou_share import *


#shutokou = {}
## 首都高の各JCTに接続する道路をリスト（集合でも良い）として与える
#shutokou[1] = [1,2,5]
#shutokou[2] = [1,4,8]
#shutokou[3] = [2,3,6]
#shutokou[4] = [3,4,7]
#shutokou[5] = [5,6,7,8]

#vert_edges_dict = shutokou
#IC_road = 1
#like_roads = []
#graph = euler_graphs(vert_edges_dict, IC_road, like_roads, max_time = 5, min_time = 2)
#pprint.pprint(graph)
#print(len(graph))

#xl = r"C:\Users\kota-kato\Desktop\その他\便利道具\首都高探索\JCT.xlsx"
xl = r"C:\Users\kota-kato\Desktop\atok12\JCT.xlsx"
dic = xlsx2vert_edges_dict(xl)
IC_road = "熊野町～西新宿"
like_roads = ["辰巳～葛西"]
graph = euler_graphs(dic, IC_road, like_roads, max_time = 4, min_time = 4)
pprint.pprint(graph)

