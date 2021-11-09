def group_csvs():
    fout=open("out.csv","a")
    # first file:
    # for line in open("/Users/jneto/msc/workspace/dataset/20_first/UNSW_2018_IoT_Botnet_Dataset_1.csv"):
    #     fout.write(line)
    # now the rest:
    for num in range(41,75):
        print(num)
        f = open("/Users/jneto/msc/workspace/dataset/final/UNSW_2018_IoT_Botnet_Dataset_"+str(num)+".csv")
        # f.__next__()
        for line in f:
            fout.write(line)
        f.close()
    fout.close()

def add_header_to_csv():
