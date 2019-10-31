import random
from sqlite3 import connect

max_difficulty = 100

class PasswordGenerator(object):
    def __init__(self, word_list):
        self._word_list = word_list
        self.conn = connect(self._word_list)
        self.cur = self.conn.cursor()
        self.cur.execute("select max(id) from words")
        self.max_id = self.cur.fetchone()[0]
        
    def password(self, word_count=7, difficulty=50):
        r = random.SystemRandom()

        top_id = int(self.max_id / float(max_difficulty) * difficulty)
            
        ids = [random.randint(1, top_id + 1)
               for i in range(word_count)]
        
        words = []
        
        for id in ids:
            self.cur.execute("select word from words where id = ?", (id,))
            words.append(self.cur.fetchone()[0])
            
        return " ".join(words)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        difficulty = float(sys.argv[1])
    else:
        difficulty = 50.0
        
    pg = PasswordGenerator("../wordlists/all-words.db")
    print(pg.password(difficulty=difficulty))
