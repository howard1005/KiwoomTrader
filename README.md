Kiwoom Trader
===

Auto stock trader using Kiwoom Open API

Any issues please report to <howard170627@gmail.com>

# Install Kiwoom Open API

- [Open API](https://www3.kiwoom.com/nkw.templateFrameSet.do?m=m1408000000)

# Config

- DB config (Modify DATABASE_CONFIG in `config/dbConfig.py`) 
    + `host` : ip address of DB (default : localhost)
    + `dbname` : name of connected DB
    + `user` : user name of connected DB
    + `password` : password of user (default : password)
    + `port` : port of connected DB (default : 3306)

- Make DB table
    ```python
    python kiwoom/kiwoom_db.py
    ```  
  
# Run
   ```python
   python __init__.py
   ```