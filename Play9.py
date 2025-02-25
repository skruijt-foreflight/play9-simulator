import sys
import random
from collections import Counter
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QProgressBar, QLabel, QTextEdit,
                             QSpinBox, QHBoxLayout, QGroupBox)
from PyQt6.QtCore import QThread, pyqtSignal

RANKS = [-5, -3, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
N_PLAYERS = 6
N_SIMULATIONS = 100000

class SimulationConfig:
    def __init__(self, target_score=6, num_rounds=7):
        self.target_score = target_score
        self.num_rounds = num_rounds

class SimulationWorker(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal(dict)

    def __init__(self, config):
        super().__init__()
        self.config = config

    def play_turn(self, hand):
        freq = Counter(hand)
        return sum((count % 2) * rank for rank, count in freq.items())

    def calculate_best_move(self, hand, drawn_card):
        current_score = self.play_turn(hand)
        best_score = current_score
        best_pos = -1

        for i in range(len(hand)):
            temp_hand = hand.copy()
            temp_hand[i] = drawn_card
            new_score = self.play_turn(temp_hand)
            if new_score < best_score:
                best_score = new_score
                best_pos = i

        return best_pos

    def play_game(self):
        deck = [rank for rank in RANKS for _ in range(4)]
        random.shuffle(deck)

        hands = [[] for _ in range(N_PLAYERS)]
        for _ in range(8):
            for player in range(N_PLAYERS):
                hands[player].append(deck.pop())

        draw_pile = deck
        cards_face_up = [0] * N_PLAYERS
        game_ongoing = True

        while game_ongoing:
            for player in range(N_PLAYERS):
                if cards_face_up[player] < 8 and draw_pile:
                    drawn_card = draw_pile.pop()
                    if player == 0:
                        best_pos = self.calculate_best_move(hands[0], drawn_card)
                        if best_pos != -1:
                            hands[0][best_pos] = drawn_card
                    cards_face_up[player] += 1

            if max(cards_face_up) == 8 or not draw_pile:
                game_ongoing = False

        return self.play_turn(hands[0])

    def run(self):
        total_matches = 0
        round_stats = []

        for sim in range(N_SIMULATIONS):
            if sim % (N_SIMULATIONS // 100) == 0:
                self.progress.emit(int(sim / N_SIMULATIONS * 100))

            scores = []
            total_score = 0
            for _ in range(self.config.num_rounds):
                game_score = self.play_game()
                scores.append(game_score)
                total_score += game_score

            if total_score == self.config.target_score:
                round_stats.append(scores)
                total_matches += 1
                self.log.emit(f"Match found! Round scores: {scores}")

        probability = total_matches/N_SIMULATIONS
        results = {
            'total_matches': total_matches,
            'probability': probability,
            'round_stats': round_stats[:5],
            'target_score': self.config.target_score,
            'num_rounds': self.config.num_rounds
        }
        self.progress.emit(100)
        self.finished.emit(results)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Play Nine Simulator")
        self.setMinimumSize(700, 600)

        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        # Title
        title = QLabel("Play Nine Card Game Simulator")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)

        # Configuration group
        config_group = QGroupBox("Simulation Settings")
        config_layout = QHBoxLayout()
        config_group.setLayout(config_layout)

        # Target score configuration
        target_score_layout = QVBoxLayout()
        target_score_label = QLabel("Target Score:")
        self.target_score_spin = QSpinBox()
        self.target_score_spin.setRange(0, 100)
        self.target_score_spin.setValue(6)
        target_score_layout.addWidget(target_score_label)
        target_score_layout.addWidget(self.target_score_spin)
        config_layout.addLayout(target_score_layout)

        # Number of rounds configuration
        rounds_layout = QVBoxLayout()
        rounds_label = QLabel("Number of Rounds:")
        self.rounds_spin = QSpinBox()
        self.rounds_spin.setRange(1, 20)
        self.rounds_spin.setValue(7)
        rounds_layout.addWidget(rounds_label)
        rounds_layout.addWidget(self.rounds_spin)
        config_layout.addLayout(rounds_layout)

        layout.addWidget(config_group)

        # Progress bar
        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        # Status label
        self.status = QLabel("Ready to start")
        layout.addWidget(self.status)

        # Results text area
        self.results = QTextEdit()
        self.results.setReadOnly(True)
        layout.addWidget(self.results)

        # Start button
        self.start_button = QPushButton("Start Simulation")
        self.start_button.clicked.connect(self.start_simulation)
        layout.addWidget(self.start_button)

        self.worker = None

    def start_simulation(self):
        self.start_button.setEnabled(False)
        self.target_score_spin.setEnabled(False)
        self.rounds_spin.setEnabled(False)
        self.results.clear()
        self.status.setText("Simulation running...")
        self.progress.setValue(0)

        config = SimulationConfig(
            target_score=self.target_score_spin.value(),
            num_rounds=self.rounds_spin.value()
        )

        self.worker = SimulationWorker(config)
        self.worker.progress.connect(self.update_progress)
        self.worker.log.connect(self.log_message)
        self.worker.finished.connect(self.simulation_finished)
        self.worker.start()

    def update_progress(self, value):
        self.progress.setValue(value)

    def log_message(self, message):
        self.results.append(message)

    def simulation_finished(self, results):
        self.status.setText("Simulation completed!")
        self.start_button.setEnabled(True)
        self.target_score_spin.setEnabled(True)
        self.rounds_spin.setEnabled(True)

        output = "Simulation Results\n"
        output += "================\n"
        output += f"Target Score: {results['target_score']}\n"
        output += f"Number of Rounds: {results['num_rounds']}\n"
        output += f"Total matches: {results['total_matches']}\n"
        probability = results['probability']
        output += f"Probability: {probability:.6f} ({probability*100:.4f}%)\n"
        output += f"Approximately 1 in {round(1/probability)} full games\n\n"

        if results['round_stats']:
            output += "Example patterns found:\n"
            for i, pattern in enumerate(results['round_stats'], 1):
                output += f"Game {i}: {pattern} = {sum(pattern)}\n"

        self.results.setText(output)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())