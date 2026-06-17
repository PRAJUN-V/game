import json
from sqlalchemy import Column, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from game_logic import LudoGame

SQLALCHEMY_DATABASE_URL = "sqlite:///./ludo.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class GameModel(Base):
    __tablename__ = "games"

    room_id = Column(String, primary_key=True, index=True)
    state = Column(Text) # Store serialized game state

Base.metadata.create_all(bind=engine)

def save_game(room_id: str, game: LudoGame):
    db = SessionLocal()
    # To save the game, we need a way to serialize the whole LudoGame object or its state
    # For simplicity, we'll store the dictionary returned by get_state()
    state_json = json.dumps(game.get_state())
    db_game = db.query(GameModel).filter(GameModel.room_id == room_id).first()
    if db_game:
        db_game.state = state_json
    else:
        db_game = GameModel(room_id=room_id, state=state_json)
        db.add(db_game)
    db.commit()
    db.close()

def load_game(room_id: str) -> LudoGame:
    db = SessionLocal()
    db_game = db.query(GameModel).filter(GameModel.room_id == room_id).first()
    db.close()
    if db_game:
        state = json.loads(db_game.state)
        game = LudoGame(room_id)
        # Reconstruct game from state
        # (This requires a bit of extra logic in LudoGame to 'hydrate')
        game.hydrate(state)
        return game
    return None
