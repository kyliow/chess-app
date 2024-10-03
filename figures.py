import chess.svg
import numpy
import pandas
import streamlit
import chess
from plotly import graph_objects


class FigureUtils:

    def __init__(self, data: pandas.DataFrame):
        self.data = data

    def get_evaluation_graph(self):
        white_eval_to_display = numpy.where(
            self.data["evaluation_type"] == "cp",
            self.data["evaluation_value"].clip(lower=-400, upper=400),
            numpy.where(
                self.data["evaluation_type"] == "mate",
                numpy.where(self.data["evaluation_value"] >= 0, 450, -450),
                self.data["evaluation_value"],
            ),
        )

        if self.data.iloc[-1]["evaluation_value"] == 0:
            white_eval_to_display[-1] = white_eval_to_display[-2]

        df = pandas.DataFrame(
            {"ply": self.data.index, "evaluation_to_display": white_eval_to_display}
        )

        fig = graph_objects.Figure()
        fig.add_trace(
            graph_objects.Scatter(
                x=df["ply"],
                y=[450] * len(df),
                fill=None,
                mode="lines",
                line_color="rgba(0,0,0,0)",
                showlegend=False,
            )
        )
        fig.add_trace(
            graph_objects.Scatter(
                x=df["ply"],
                y=df["evaluation_to_display"],
                fill="tonexty",
                mode="lines",
                line_color="rgba(0,0,0,0)",
                showlegend=False,
                fillcolor="#424242",
            )
        )
        fig.add_trace(
            graph_objects.Scatter(
                x=df["ply"],
                y=[-450] * len(df),
                fill="tonexty",
                mode="lines",
                line_color="rgba(0,0,0,0)",
                showlegend=False,
                fillcolor="#e3e3e3",
            )
        )
        fig.add_hline(y=0, line_color="#B2B0AE")
        fig = streamlit.plotly_chart(fig)
        return fig

    def get_chess_board_images(self, is_player_white: bool):
        orientation = chess.WHITE if is_player_white else chess.BLACK

        images = []
        board = chess.Board()
        img = chess.svg.board(board, size=500, orientation=orientation)
        images.append(img)

        for i, row in self.data.iterrows():
            move = row["move"]
            print(i, move)
            
            board.push(chess.Move.from_uci(move))
            img = chess.svg.board(board, size=500, orientation=orientation)
            images.append(img)

        return images
