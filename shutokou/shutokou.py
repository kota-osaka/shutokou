import copy
#from hashlib import new
import pandas as pd
import openpyxl
#import xlrd
import itertools


import sys
import threading

#変更前の再帰関数の実行回数の上限を表示
print(sys.getrecursionlimit())

sys.setrecursionlimit(671088640) #640MB
threading.stack_size(1024*1024)  #2の20乗のstackを確保=メモリの確保

#変更後の再帰関数の実行回数の上限を表示
print(sys.getrecursionlimit())


# Eulerable と requestable に分けた方がいいかも？
def Is_likeable(vert_edges_dict, path, IC_road, like_roads = []):

    prime_JCT = [JCT for JCT, branch in vert_edges_dict.items() if IC_road in branch]

    for road in like_roads: #通りたい道を通っているか
        if road not in path :
            return False

    if IC_road not in path : # ICから出るため（入るため）の道
        return False

    for JCT, branch in vert_edges_dict.items():
        deg_JCT = len(branch) + len(path) - len(set(branch + path))
        if deg_JCT == 1 : #そのJCTで折り返すようなルートになってしまう
            return False
        #if (JCT in prime_JCT) and deg_JCT == 0 :#スタートとゴールを通っているか
        #    return False
    return True


def Is_euler_graph(vert_edges_dict, path, regard_same_road):

    for JCT, branch in vert_edges_dict.items():
        deg_JCT = 0
        for road in branch :
            deg_JCT += path.count(road)
        if deg_JCT % 2 == 1:
            return False

        # 互いに移動できない道を持つJCTがある場合、特殊な判定を行う。（互いに移動できない道が2組以上ある場合には未対応。なお、互いに移動できない道は3本以上であっても可）
        if JCT in regard_same_road.keys():
            regard_same_road_num = 0
            for road in regard_same_road[JCT]:
                regard_same_road_num += path.count(road)
            if deg_JCT - regard_same_road_num < regard_same_road_num:
                return False

    return True


#道を走行時間に変換する関数。未着手
def run_time(road, traffic_jam = False):
    # なんか処理を書く
    return 1


#走行時間を計算する関数。混み具合を考える？短すぎるときの処理は、別途作った方が良い。
def Is_timeable(path, max_time, min_time, Is_simple = False):

    if len(path) > 10 : # そもそもpathが多すぎたら問答無用でFalseを返してもよい。数は要調整
        return False

    run_time_all = 0
    for road in path : run_time_all += run_time(road)
    if run_time_all > max_time :
        return False
    if Is_simple and run_time_all < min_time :
        return False

    return True


def path2dict(vert_edges_dict, path):
    path_dict = {}
    for JCT, branch in vert_edges_dict.items():
        path_dict[JCT] = []
        for road in branch:
            path_dict[JCT] += [road]*path.count(road)

    return path_dict

#時間内に行って帰ってこれる範囲でのvert_edges_dictを作成する
def extract_reachable_road(vert_edges_dict, IC_road, max_time):

    capa_time = max_time/2
    reachable_path = {IC_road}
    shortest_time = run_time(IC_road)

    JCTs = []
    while shortest_time < capa_time:
        new_path = set()
        for JCT, branch in vert_edges_dict.items():
            if JCT in JCTs : continue
            if len(reachable_path & set(branch)) > 0:
                JCTs.append(JCT)
                for path in list(set(branch) - reachable_path):
                    new_path = new_path.union(branch)

        new_path_runtime = [run_time(path) for path in list(new_path)]
        reachable_path = reachable_path.union(new_path)

        if new_path_runtime == [] : break
        shortest_time += min(new_path_runtime)

    # max_time の半分の時間で到達可能な範囲の首都高。切断辺を含む。
    reachable_vert_edges_dict = path2dict(vert_edges_dict, list(reachable_path))

    # 切断辺を消す。
    cutting_edge = True
    while cutting_edge:
        cutting_edge = False
        del_branch = []
        for JCT, branch in reachable_vert_edges_dict.items():
            if len(branch) == 1:
                reachable_path.discard(branch[0])
                reachable_vert_edges_dict = path2dict(vert_edges_dict, list(reachable_path))
                cutting_edge = True

    return reachable_vert_edges_dict

#JCT をスタートする道から近い順にヒエラルキー付けする
#JCT をスタートする道から近い順にヒエラルキー付けす
def hierarchfy_JCT(vert_edges_dict, IC_road, regard_same_road, split_txt="～"):
    zero_JCT = [JCT for JCT, branch in vert_edges_dict.items() if (IC_road in branch)]

    cover_road = [IC_road]
    cover_JCT = zero_JCT # list の挙動で不安
    JCT_hierarchy = [zero_JCT] # list の挙動で不安
    mintime_each_hierarchy = [run_time(IC_road)]

    JCT_num = len(vert_edges_dict.keys())
    for _ in range(JCT_num):
        mintime = 999999
        new_JCT = []
        for JCT in JCT_hierarchy[-1]:
            new_road = [road for road in vert_edges_dict[JCT] if (road not in cover_road)]
            mintime = min([mintime] + [run_time(road) for road in new_road])
            cover_road.append(new_road)
            for road in new_road:
                JCT_0 = road.split(split_txt)[0]
                JCT_1 = road.split(split_txt)[1]
                if JCT_0 not in cover_JCT: new_JCT.append(JCT_0)
                if JCT_1 not in cover_JCT: new_JCT.append(JCT_1)

        mintime_each_hierarchy.append(mintime)
        #if sum(mintime_each_hierarchy) > max_time:
        #    return JCT_hierarchy

        new_JCT = list(set(new_JCT) - set(cover_JCT))
        cover_JCT = cover_JCT + new_JCT
        JCT_hierarchy.append(new_JCT)
        if len(cover_JCT) == JCT_num:
            break #実質ここでreturn

    return JCT_hierarchy, mintime_each_hierarchy

#def extract_simple_paths(vert_edges_dict, IC_road, like_roads, max_time, regard_same_road, split_txt="～"):
#    #JCT_hierarchy = hierarchfy_JCT(vert_edges_dict, IC_road, like_roads, max_time, regard_same_road, split_txt="～")
#    simple_paths = []
#    return

# 与えられたJCTのみを通るようなグラフを作成
def JCTs2dict(use_JCTs, vert_edges_dict, split_txt="～"):
    new_vert_edges_dict = {}
    JCTs = vert_edges_dict.keys()
    unuse_JCTs = [JCT for JCT in JCTs if (JCT not in use_JCTs)]
    #for unuse_JCT in unuse_JCTs:
    #    del vert_edges_dict[unuse_JCT]
    for JCT in use_JCTs:
    #for key, val in vert_edges_dict.items():
        new_val = [path for path in vert_edges_dict[JCT] if ((path.split(split_txt)[0] not in unuse_JCTs) and (path.split(split_txt)[1] not in unuse_JCTs))]
        new_vert_edges_dict[JCT] = new_val
    return new_vert_edges_dict

# 確実な切断辺があるかのチェック
def Is_certain_cut(combinate_element, vert_edges_dict, generators, split_txt="～"):
    use_JCT =[]
    for hie in combinate_element:
        use_JCT = use_JCT + hie
    #use_JCT = [JCT for sublist in combinate_element for JCT in sublist]
    #vert_edges_dict = JCTs2dict(JCTs, vert_edges_dict, split_txt="～")
    JCTs = vert_edges_dict.keys()
    unuse_JCT = [JCT for JCT in JCTs if (JCT not in use_JCT)]
    if len(combinate_element) > 1:
        for JCT in combinate_element[-2]:
            paths = vert_edges_dict[JCT]
            unuse_paths = [path for path in paths if ((path.split(split_txt)[0] in unuse_JCT) or (path.split(split_txt)[1] in unuse_JCT))]
            if len(paths) - len(unuse_paths) < 2 : 
                return True

    for JCT in combinate_element[-1]:
        next_hie = generators[len(combinate_element)][-1]
        paths = vert_edges_dict[JCT]
        remain_paths = [path for path in paths if ((path.split(split_txt)[0] in next_hie) or (path.split(split_txt)[1] in next_hie))]
        certain_paths = [path for path in paths if ((path.split(split_txt)[0] in combinate_element[-2]) or (path.split(split_txt)[1] in combinate_element[-2]))]
        if len(remain_paths) + len(certain_paths) < 2 : 
            return True

    return False

# 枝刈りが入った時
def find_next_situ(situation, max_situation):
    max_situation = max_situation[:len(situation)]
    bool_situation = [(situation[i]==max_situation[i]) for i in range(len(situation))]
    last_False = len(bool_situation) - bool_situation[::-1].index(False) -1

    new_situation = situation[:last_False + 1]
    new_situation[last_False] += 1

    return new_situation


# 組み合わせ全探索
# generators:べき集合たち
# situation:どの状態か（defaultは[0]）、
# max_situation:[len(gen)-1 for gen in generators]、
# combinate_elementは今考えている組み合わせ
# combinationsは良さげな組み合わせ
# reverse_mode: situationの作り直し中
def my_combinate(generators, situation, max_situation, combinate_element, combinations, reverse_mode, vert_edges_dict, count_test):
    #if count_test == 0:
    #    print(generators)
    #count_test += 1
    #if count_test == 1700:
    #    print("err?")
    #print(count_test)
    if reverse_mode: reverse_mode = False # find_next_situの直後
    else:
        if len(situation) < len(max_situation) : 
            situation.append(0)
        elif situation[-1] != max_situation[len(situation)-1] : 
            situation[-1] += 1
        else : 
            situation = find_next_situ(situation, max_situation)
        combinate_element = [generators[hie][inline_num] for hie, inline_num in enumerate(situation)]


    
    if Is_certain_cut(combinate_element, vert_edges_dict, generators):
        situation = find_next_situ(situation, max_situation)
        combinate_element = [generators[hie][inline_num] for hie, inline_num in enumerate(situation)]
        reverse_mode = True
    else : 
        print(combinations)
        combinations.append(combinate_element)

    if situation != max_situation:
        combinations = my_combinate(generators, situation, max_situation, combinate_element, combinations, reverse_mode, vert_edges_dict, count_test)

    return combinations


def divide_dict(ve_dict, main_JCTs, sub_JCTs, split_text="～"):

    JCTs = list(ve_dict.keys())
    remain_JCTs = list(set(JCTs) - set(main_JCTs + sub_JCTs))

    new_main_JCT = remain_JCTs[0]
    adjacent_JCTs = [road.split(split_text)[int(not road.split(split_text).index(new_main_JCT))] for road in ve_dict[new_main_JCT]]
    main_JCTs.append(new_main_JCT)
    sub_JCTs =list(set(sub_JCTs + list(set(adjacent_JCTs) - set(main_JCTs))))
    #a = len(JCTs)
    #b = len(main_JCTs)
    #c = len(sub_JCTs)
    #test = len(JCTs) - len(main_JCTs) - len(sub_JCTs)
    #print(f"{JCTs} - {main_JCTs} - {sub_JCTs}")
    #print(f"{len(JCTs)} - {len(main_JCTs)} - {len(sub_JCTs)} = {len(JCTs) - len(main_JCTs) - len(sub_JCTs)}")
    if (len(JCTs) - len(main_JCTs) - len(sub_JCTs)) == 0:
        return main_JCTs, sub_JCTs
    else :
        main_JCTs, sub_JCTs = divide_dict(ve_dict, main_JCTs, sub_JCTs)

    return main_JCTs, sub_JCTs

def saiki_test(num):
    print(num)
    num+=1
    if True:
        num = saiki_test(num)
    return num

# 本命
def euler_graphs(vert_edges_dict, IC_road, like_roads, max_time = 180, min_time = 2, regard_same_road={1:[1,5]}):
    #test = saiki_test(0)


    roads_twise = []
    for roads in vert_edges_dict.values(): roads_twise += roads

    roads_all = list(set(roads_twise))
    roads_num = len(roads_all) # ここまでは前情報として持たせてもよい

    #階層化
    JCT_hierarchy, mintime_each_hierarchy = hierarchfy_JCT(vert_edges_dict, IC_road, regard_same_road, split_txt="～")
    reachable_hierarchy = 0
    for i,val in enumerate(mintime_each_hierarchy):
        if sum(mintime_each_hierarchy[ : i+1 ]) > (max_time / 2) : reachable_hierarchy = i+1 #行けてもこの層まで

    #行ける階層までで、階層ごとにべき集合を作成
    hierarchy_tree = []
    for val in JCT_hierarchy[ :reachable_hierarchy]:
        hierarchy_power = []
        for i in range(2**len(val)):
            temp_set = []
            for j in range(len(val)):
                if( (i>>j) & 1):
                    temp_set.append(val[j])
                    
            if len(temp_set) > 0: hierarchy_power.append(temp_set)
        hierarchy_tree.append(hierarchy_power)

    #i層のべき集合から一つ選ぶ。選ぶたびに、良いグラフになりそうか（確実な切断辺がないか、時間を過ぎていないか）を判定する。
    max_situation = [len(hierarchy_power) for hierarchy_power in hierarchy_tree]
    #combinations = my_combinate(hierarchy_tree, [0], max_situation, [], [], False, vert_edges_dict)
    situation = [len(hierarchy_tree[0]) - 1]
    max_situation = [len(hierarchy_power)-1 for hierarchy_power in hierarchy_tree]
    max_situation = [2, 14, 14, 254]

    combinate_element = [hierarchy_tree[0][-1], 14]
    combinations = []
    reverse_mode = False
    combinations = my_combinate(hierarchy_tree, situation, max_situation, combinate_element, combinations, reverse_mode, vert_edges_dict,0)
    #combinations = [[['熊野町', '西新宿'], ['大橋', '板橋']], [['熊野町', '西新宿'], ['大橋', '板橋'], ['谷町', '江北']], [['熊野町', '西新宿'], ['大橋', '板橋'], ['谷町', '神田橋', '江北']], [['熊野町', '西新宿'], ['大橋', '板橋'], ['大井', '江北']], [['熊野町', '西新宿'], ['大橋', '板橋'], ['大井', '江北'], ['芝浦', '小菅']]]
    #combinations = [[['熊野町', '西新宿'], ['竹橋', '三宅坂'], ['神田橋', '大井'], ['有明', '江戸橋', '東海', '芝浦', '箱崎', '浜崎橋']]]
    #Is_finish = False
    #count_test = 0
    #while not Is_finish:
    #    hierarchy_tree, situation, max_situation, combinate_element, combinations, reverse_mode, vert_edges_dict,count_test, Is_finish = my_combinate(hierarchy_tree, situation, max_situation, combinate_element, combinations, reverse_mode, vert_edges_dict,count_test)
    con_nagasa = len(combinations)

    # 必ず通るようなJCTのリストを作成し、辞書を作る
    cand_dicts = []
    for comnbination in combinations:
        JCTs = [JCT for subset in comnbination for JCT in subset ]
        #cand_dicts.append(JCTs2dict(JCTs, vert_edges_dict, split_txt="～"))
        cand_dict = JCTs2dict(JCTs, vert_edges_dict)
        main_JCTs = [] 
        sub_JCTs = []
        main_JCTs, sub_JCTs = divide_dict(cand_dict, main_JCTs, sub_JCTs, split_text="～")
        print(cand_dict)
        main_JCT = [JCTs[0]]

    for cand_dict in cand_dicts:
        main_JCT = []


    test = {'熊野町': ['熊野町～西新宿', '熊野町～竹橋'], '西新宿': ['熊野町～西新宿', '西新宿～三宅坂'], '竹橋': ['熊野町～竹橋', '竹橋～三宅坂', '神田橋～竹橋', '神田橋～竹橋'], '三宅坂': ['西新宿～三宅坂', '竹橋～三宅坂'], '神田橋': ['江戸橋～神田橋', '箱崎～神田 橋', '神田橋～竹橋'], '江戸橋': ['江戸橋～神田橋','江戸橋～西銀座'],  '芝浦': ['大井～芝浦', '有明～芝浦', '芝浦～浜崎橋'], '箱崎': ['箱崎～神田橋','箱崎～京橋'], '西銀座':['江戸橋～西銀座','西銀座～京橋'],'京橋':['西銀座～京橋','箱崎～京橋']}
    



    ##まずは単純辺のみのグラフを考え、最低限の要素を満たしているか判定する
    #simple_paths = []

    #for i in range(2**roads_num):
    #    simple_path = []
    #    for j in range(roads_num):
    #        if( (i>>j) & 1):
    #            simple_path.append(roads_all[j])

    #    #ここで好ましいルートになりそうか判定。
    #    if Is_likeable(vert_edges_dict, simple_path, IC_road, like_roads) and Is_timeable(simple_path, max_time, min_time, Is_simple = True):
    #        simple_paths.append(simple_path)
    #        print(len(simple_paths)) #test
    #        if len(simple_paths) > 20:
    #            break

    #test1 = len(simple_paths) # ここが多いと死ぬ
    ## 2回通る道を決め、走行する道を確定する
    #paths = []

    #for simple_path in simple_paths:
    #    simple_roads_num = len(simple_path)

    #    for i in range(2**simple_roads_num):
    #        path = copy.deepcopy(simple_path)
    #        for j in range(simple_roads_num):
    #            if ( (i>>j) & 1):
    #                path.append(simple_path[j])

    #        if Is_euler_graph(vert_edges_dict, path, regard_same_road) and Is_timeable(simple_path, max_time, min_time):
    #            paths.append(path2dict(vert_edges_dict, path))


    #return paths
    return 1

def xlsx2vert_edges_dict(xl, wild_JCT_mode=False):
    #shutokou_xl = pd.read_excel(xl)
    shutokou_xl = pd.read_excel(xl)
    vert_edges_dict = {}

    for _, item in shutokou_xl.iterrows():
        JCTs = [item["JCT(下)"], item["JCT(上)"]]
        road = item["道"]
        if (wild_JCT_mode == False) and ("wild_card" in JCTs) : continue

        for JCT in JCTs:
            if JCT in vert_edges_dict.keys():
                vert_edges_dict[JCT].append(road)
            else:
                vert_edges_dict[JCT] = [road]

    #if wild_JCT_mode : pass
    #else: 
    #    vert_edges_dict.pop("wild_card")
    return vert_edges_dict


#def paths2roads(paths, vert_edges_dict):

#    for path in paths:


#    return
               


import random

metroEXPWY = {\
    "西新宿":["西新宿-大橋","西新宿-熊野町"],\
    "大橋":["西新宿-大橋","大橋-大井"],\
    "大井":["大橋-大井","大井-東海","大井-芝浦","大井-昭和島","大井-有明"],\
    "東海":["東海-川崎浮島","東海-昭和島","東海-大井"],\
    "川崎浮島":["川崎浮島-東海","川崎浮島-大師","川崎浮島-大黒"]\
    }
def make_path(JCT_dict, pathlog, JCTlog, in_JCT = "西新宿"):
    return
    temp_JCT = in_JCT
    next_path_candidate = JCT_dict[temp_JCT] ## next_path_candidate = [道1, 道2...]

    while len(next_path_candidate) >= 1: ## >=にしておかないと上手く動かない泣
        try: ## 次数が1以下の場合はGoalにならないといけない？
            print("continue")
            next_path = random.choice(next_path_candidate) ## next_path = 道1
            print(next_path)
            print(temp_JCT) # いらない？
            pathlog.append(next_path)
            JCTlog.append(temp_JCT)
            JCT_dict[temp_JCT].remove(next_path) ## JCT_nにおいて通った道は消しておく
            for k,v in JCT_dict.items(): ## 逆引き。O(n)なので改良の余地あり？
                # print("key="+str(k))
                # print("val="+str(v))

                if next_path in v:
                    temp_JCT = k
                    print(temp_JCT)
                    break
            JCT_dict[temp_JCT].remove(next_path) ## JCT_n+1において元来た道は消しておく
            next_path_candidate = JCT_dict[temp_JCT]
        except ValueError:
            break
    else:
        print("trip is over...")    
    ## JCTで折り返すジャンキーに対応できてないと思う
    ## せっかく二重にしたのにいっぺんに消えてると思う

pathlog_dayo = []
JCTlog_dayo = []
make_path(metroEXPWY, pathlog_dayo, JCTlog_dayo, "西新宿")
#print(pathlog_dayo)
#print(JCTlog_dayo)

## {key=JCT, value=パス[]}
## {大井:[湾岸、羽田、C2]}
## 今のdictにはICの情報は無い。道の定義はJCT間の道。
## 逆引きの辞書があった方がいいかも？今はJCT→接続道はある。その逆が無い。


