import csv

train_path = "C:\\Users\\jacob\\Documents\\Projects\\CSGO_Train\\images\\train_labels.csv"
test_path = "C:\\Users\\jacob\\Documents\\Projects\\CSGO_Train\\images\\test_labels.csv"

def fix(path):
    f = open(path, "r")
    reader = csv.reader(f)

    rows = list(reader)
    for row in rows[1:]:
        print(row)
        if int(row[4]) > int(row[1]):
            row[4] = row[1]
        if int(row[4]) <= 0:
            row[4] = "0"
        if int(row[6]) > int(row[1]):
            row[6] = row[1]
        if int(row[6]) <= 0:
            row[6] = "0"

        if int(row[5]) > int(row[2]):
            row[5] = row[2]
        if int(row[5]) <= 0:
            row[5] = "0"
        if int(row[7]) > int(row[2]):
            row[7] = row[2]

        if int(row[7]) <= 0:
            row[7] = "0"

        if int(row[5]) > int(row[7]):
            tmp = row[5]
            row[5] = row[7]
            row[7] = tmp
    f.close()

    f = open(path, "w", newline="")
    writer = csv.writer(f)
    writer.writerows(rows)
    f.close()


fix(train_path)
fix(test_path)
