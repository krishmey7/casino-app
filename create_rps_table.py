import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projet_casino.settings')
django.setup()

from django.db import connection

def create_rps_table():
    with connection.cursor() as cursor:
        # Vérifier si la table existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='rock_paper_scissors_rockpaperscissorsgame'
        """)
        result = cursor.fetchone()
        
        if result:
            print("La table existe déjà.")
            return
        
        # Créer la table manuellement
        cursor.execute("""
            CREATE TABLE "rock_paper_scissors_rockpaperscissorsgame" (
                "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                "bet_amount" decimal NOT NULL,
                "player1_choice" varchar(10) NULL,
                "player2_choice" varchar(10) NULL,
                "status" varchar(10) NOT NULL,
                "created_at" datetime NOT NULL,
                "finished_at" datetime NULL,
                "player1_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
                "player2_id" integer NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
                "winner_id" integer NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED
            )
        """)
        
        # Créer les index
        cursor.execute("""
            CREATE INDEX "rock_paper_scissors_rockpaperscissorsgame_player1_id_52b9a6f6" 
            ON "rock_paper_scissors_rockpaperscissorsgame" ("player1_id")
        """)
        
        cursor.execute("""
            CREATE INDEX "rock_paper_scissors_rockpaperscissorsgame_player2_id_3205b4d5" 
            ON "rock_paper_scissors_rockpaperscissorsgame" ("player2_id")
        """)
        
        cursor.execute("""
            CREATE INDEX "rock_paper_scissors_rockpaperscissorsgame_winner_id_eddb2836" 
            ON "rock_paper_scissors_rockpaperscissorsgame" ("winner_id")
        """)
        
        print("Table rock_paper_scissors_rockpaperscissorsgame créée avec succès.")

if __name__ == "__main__":
    create_rps_table()
