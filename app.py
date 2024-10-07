import os
from datetime import datetime

import streamlit

from chess_utils import WHITE_SYMBOL, ChessUtils
from figures import FigureUtils


def main():
    streamlit.title("Chess Review App")

    username = streamlit.sidebar.text_input(label="Chess.com username:")

    streamlit.sidebar.write(
        "Input year and month to download the PGN file from Chess.com:"
    )
    year = streamlit.sidebar.number_input(
        label="Year:", value=datetime.today().year, max_value=datetime.today().year
    )
    month = streamlit.sidebar.number_input(
        label="Month:", value=datetime.today().month, min_value=1, max_value=12
    )
    is_delete_all_analysed_games = streamlit.sidebar.button("Delete all analysed games")        

    chess_utils = ChessUtils(username=username, year=year, month=month)

    if is_delete_all_analysed_games:
        chess_utils.delete_all_analysed_games()

    all_games = chess_utils.load_all_games()
    if all_games is None:
        return

    chosen_game_key = streamlit.selectbox("Choose a game.", all_games)

    # if "previous_chosen_game_key" not in streamlit.session_state:
    #     streamlit.session_state["previous_chosen_game_key"] = None
    #     streamlit.session_state["chess_board_images"] = None
    #     streamlit.session_state["chess_board_images_counter"] = None

    # if streamlit.session_state["previous_chosen_game_key"] != chosen_game_key:
    #     streamlit.session_state["previous_chosen_game_key"] = chosen_game_key
    #     del streamlit.session_state["chess_board_images"]
    #     del streamlit.session_state["chess_board_images_counter"]

    is_generate_game_stat = streamlit.button("Generate game analysis", type="primary")

    progress_bar = streamlit.progress(0.0)

    if (
        not is_generate_game_stat
        # and "chess_board_images" not in streamlit.session_state
    ):
        return

    data = chess_utils.create_game_dataframe(
        game_key=chosen_game_key, progress_bar=progress_bar
    )

    # streamlit.data_editor(data)

    # streamlit.write("### Evaluation Graph")
    # fig_utils = FigureUtils(data=data)
    # _ = fig_utils.get_evaluation_graph()

    # if "chess_board_images" not in streamlit.session_state:
    #     is_player_white = WHITE_SYMBOL in chosen_game_key
    #     chess_board_images = fig_utils.get_chess_board_images(
    #         is_player_white=is_player_white
    #     )
    #     streamlit.session_state["chess_board_images"] = chess_board_images
    # else:
    #     chess_board_images = streamlit.session_state["chess_board_images"]

    # number_of_plies = len(chess_board_images)

    # def _next():
    #     streamlit.session_state["chess_board_images_counter"] += 1

    # def _prev():
    #     streamlit.session_state["chess_board_images_counter"] -= 1

    # if "chess_board_images_counter" not in streamlit.session_state:
    #     streamlit.session_state["chess_board_images_counter"] = 0

    # container = streamlit.empty()
    # cols = streamlit.columns(2)
    # with cols[1]:
    #     streamlit.button("Next ➡️", on_click=_next, use_container_width=True)
    # with cols[0]:
    #     streamlit.button("⬅️ Previous", on_click=_prev, use_container_width=True)

    # with container.container():
    #     img = chess_board_images[
    #         streamlit.session_state["chess_board_images_counter"] % number_of_plies
    #     ]
    #     streamlit.image(img, use_column_width=True)


if __name__ == "__main__":
    main()
