import io
import json
import os
import re
import urllib
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Tuple

import pandas
import streamlit
from chess import pgn
from streamlit.delta_generator import DeltaGenerator

WHITE_SYMBOL = "⬜"
BLACK_SYMBOL = "⬛"

WIN_SYMBOL = "✅"
DRAW_SYMBOL = "🟰"
LOSE_SYMBOL = "⛔"


class ChessUtils:
    def __init__(self, username: str, year: int, month: int):
        self.username = username
        self.year = year
        self.month = month

    def _download_games_from_url(self):
        url = (
            f"https://api.chess.com/pub/player/{self.username}"
            + f"/games/{self.year}/{self.month:02}"
        )

        try:
            response = urllib.request.urlopen(url)
            if response.status == 200:
                response = response.read().decode("utf-8")
                response_json = json.loads(response)
                return response_json

            else:
                print(f"Error: {response.status}")
                return None

        except Exception as e:
            print("Error while downloading games: ", e)
            return None

    def load_all_games(self) -> Dict[str, pgn.Game]:

        response_json = self._download_games_from_url()

        if response_json is None:
            streamlit.error(
                "Unable to query games from username given. Please input the correct username.",
                icon="🚨",
            )
            return None

        all_games = {}
        for response_game in response_json["games"][::-1]:
            pgn_file = io.StringIO(response_game["pgn"])
            game = pgn.read_game(pgn_file)

            datetime_format_in = "%Y.%m.%d %H:%M:%S"
            datetime_format_out = "%Y.%m.%d - %H.%M.%S"
            key_date = (
                datetime.strptime(
                    f"{game.headers['UTCDate']} {game.headers['UTCTime']}",
                    datetime_format_in,
                )
                + timedelta(hours=8)
            ).strftime(datetime_format_out)

            if game.headers["White"] == self.username:
                white_or_black = WHITE_SYMBOL
                opponent = game.headers["Black"]
            else:
                white_or_black = BLACK_SYMBOL
                opponent = game.headers["White"]
            wdl_status = (
                WIN_SYMBOL
                if self.username in game.headers["Termination"]
                else (
                    DRAW_SYMBOL
                    if "drawn" in game.headers["Termination"]
                    else LOSE_SYMBOL
                )
            )
            key = f"{key_date} [{white_or_black} - {wdl_status} vs {opponent}]"

            all_games[key] = game

        self.all_games = all_games

        return all_games

    def _describe_move(
        self,
        winning_probability_before: float,
        winning_probability_after: float,
        current_move: str,
        best_move: str,
        previous_descriptor: str,
    ) -> Tuple[float, str]:
        diff = max(0.0, winning_probability_before - winning_probability_after)

        if diff == 0.0 or current_move == best_move:
            descriptor = "Best"
        elif 0.0 < diff <= 0.02:
            descriptor = "Excellent"
        elif 0.02 < diff <= 0.05:
            descriptor = "Good"
        elif 0.05 < diff <= 0.1:
            descriptor = "Inaccuracy"
        elif 0.1 < diff <= 0.2:
            descriptor = "Mistake"
        else:
            descriptor = "Blunder"

        if (
            previous_descriptor in ["Mistake", "Blunder", "Miss"]
            and descriptor == "Best"
        ):
            descriptor = "Great Move"
        elif previous_descriptor in ["Mistake", "Blunder", "Miss"] and descriptor in [
            "Mistake",
            "Blunder",
        ]:
            descriptor = "Miss"

        return diff, descriptor

    def _get_evaluation_from_stockfish_api(self, fen: str, depth: int = 12) -> Dict:
        stockfish_api_url = "https://stockfish.online/api/s/v2.php"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
        }
        params = {"fen": fen, "depth": depth}

        request = urllib.request.Request(
            f"{stockfish_api_url}?{urllib.parse.urlencode(params)}", headers=headers
        )
        response = urllib.request.urlopen(request)

        return json.loads(response.read().decode("utf-8"))

    def create_game_dataframe(
        self, game_key: str, progress_bar: DeltaGenerator
    ) -> pandas.DataFrame:
        path = Path.cwd() / "analysed_games"
        filename = f"{game_key[:21]}.csv"

        try:
            data = pandas.read_csv(path / filename)
            progress_bar.progress(1.0, "Analysis loaded.")

        except Exception:
            game: pgn.Game = self.all_games[game_key]
            data = pandas.DataFrame()

            total_plies = len(game.end().board().move_stack)

            board = game.board()
            fen_list = [board.fen()]
            for i, ply in enumerate(game.mainline_moves()):
                progress_bar.progress(
                    i / total_plies, "Analysis in progress. Please wait."
                )

                # Get evaluation of the previous ply
                result = self._get_evaluation_from_stockfish_api(fen=fen_list[-1])
                if result["success"]:
                    best_move = re.search(
                        r"bestmove\s([a-h][1-8][a-h][1-8])", result["bestmove"]
                    ).group(1)
                    sub_data = pandas.DataFrame(
                        {
                            "player": [i % 2],
                            "move": [ply],
                            "eval": [result["evaluation"]],
                            "mate": [result["mate"]],
                            "best_move": [best_move],
                            "continuation": [result["continuation"]],
                        }
                    )
                else:
                    streamlit.write(result)
                    streamlit.write(fen_list[-1])
                    streamlit.write(f"i - {result['error']}")
                    sub_data = pandas.DataFrame()

                board.push(ply)

                fen = board.fen()
                fen_list.append(fen)

                data = pandas.concat([data, sub_data], ignore_index=True)

            data.to_csv(path / filename, index_label=False)
            progress_bar.progress(1.0, "Analysis completed and saved.")

        return data

    @staticmethod
    def delete_all_analysed_games():
        csv_files = list((Path.cwd() / "analysed_games").glob("*.csv"))
        for file in csv_files:
            os.remove(file)
        streamlit.success("Sucessfully delete all analysed games!", icon="✅")


if __name__ == "__main__":
    cu = ChessUtils("ababov", 2024, 9)
    response = cu._download_games_from_url()
    print(response)
