import pymysql
import config.dbConfig as config
from kiwoom.kiwoom_data import real_data

class kiwoom_db():
    def __init__(self):
        self.db = pymysql.connect(
            user=config.DATABASE_CONFIG['user'],
            passwd=config.DATABASE_CONFIG['password'],
            host=config.DATABASE_CONFIG['host'],
            db=config.DATABASE_CONFIG['dbname'],
            charset='utf8'
        )
        print("DB Connect : %s" % self.db)
        self.cursor = self.db.cursor(pymysql.cursors.DictCursor)
        print("DB cursor : %s" % self.cursor)

    def db_insert(self, table_name, stock_no, fid_dict):
        sql = "INSERT INTO {} (timestamp,stock_no,{}) VALUES ((now()),{},{});".format(table_name,\
                                                        "".join(["{},".format(key) for key in fid_dict.keys()])[:-1],\
                                                        stock_no,\
                                                        "".join(["'{}',".format(val) for val in fid_dict.values()])[:-1])
        print("db insert!!")
        # print(sql)
        self.cursor.execute(sql)
        self.db.commit()

    def db_create_table(self, table_name, data_list):
        sql = "SHOW TABLES LIKE '{}';".format(table_name)
        if self.cursor.execute(sql) != 0:
            print("err : exist table {}".format(table_name))
            return
        sql = "CREATE TABLE {} (\nseq INT NOT NULL AUTO_INCREMENT,\ntimestamp TIMESTAMP DEFAULT '0000-00-00 00:00:00',\nstock_no VARCHAR(32),\n{} {}\n) ENGINE=MYISAM DEFAULT CHARSET=utf32;"\
            .format(table_name,"".join(["{} VARCHAR(32),\n".format(col) for col in data_list]),"PRIMARY KEY (seq,timestamp)")
        # print("create table \n {}".format(sql))
        self.cursor.execute(sql)
        self.db.commit()


if __name__ == '__main__':
    kb = kiwoom_db()
    for name,table in real_data.items():
        kb.db_create_table(name, list(table.keys()))