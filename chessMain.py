import pygame as pg
import chess_engine as chessEngine
import smartMoveFinder as AI_move
from network import Network, NetworkError

# Initialize pygame to get display info
pg.init()
display_info = pg.display.Info()
SCREEN_WIDTH = display_info.current_w
SCREEN_HEIGHT = display_info.current_h

DIMENSION = 8
MAX_SIZE = int(min(SCREEN_WIDTH * 0.8, SCREEN_HEIGHT * 0.8))
SQ_SIZE = max(1, MAX_SIZE // DIMENSION)
BOARD_PIXEL_SIZE = SQ_SIZE * DIMENSION
WIDTH = HEIGHT = BOARD_PIXEL_SIZE

BOARD_WIDTH = int(WIDTH * 0.75)
MOVE_LOG_WIDTH = WIDTH - BOARD_WIDTH
MAX_FPS = 60
IMAGES = {}
SOUNDS = {}
colors = [pg.Color("white"), pg.Color("lightblue")]

def load_images():
    pieces = ['wP', 'wR', 'wN', 'wB', 'wQ', 'wK', 'bP', 'bR', 'bN', 'bB', 'bQ', 'bK']
    for piece in pieces:
        IMAGES[piece] = pg.transform.scale(pg.image.load("images1/" + piece + ".png"), (SQ_SIZE, SQ_SIZE))

def load_sounds():
    """Load all sound effects for the game"""
    try:
        SOUNDS['game_start'] = pg.mixer.Sound("SFX/game-start.mp3")
        SOUNDS['move'] = pg.mixer.Sound("SFX/move-self.mp3")
        SOUNDS['capture'] = pg.mixer.Sound("SFX/capture.mp3")
        SOUNDS['castle'] = pg.mixer.Sound("SFX/castle.mp3")
        SOUNDS['promote'] = pg.mixer.Sound("SFX/promote.mp3")
        SOUNDS['check'] = pg.mixer.Sound("SFX/move-check.mp3")
        SOUNDS['game_end'] = pg.mixer.Sound("SFX/game-end.webm")
    except Exception as e:
        print(f"Error loading sounds: {e}")

def play_move_sound(move, is_check):
    """Play appropriate sound effect based on the move type"""
    try:
        if is_check:
            SOUNDS['check'].play()
        elif move.is_castle_move:
            SOUNDS['castle'].play()
        elif move.is_pawn_promotion:
            SOUNDS['promote'].play()
        elif move.piece_captured != "--":
            SOUNDS['capture'].play()
        else:
            SOUNDS['move'].play()
    except Exception as e:
        print(f"Error playing sound: {e}")

class Button:
    """Button class for menu interface"""
    def __init__(self, text, pos, size, bg_color, text_color):
        self.text = text
        self.pos = pos
        self.size = size
        self.bg_color = bg_color
        self.hover_color = (min(bg_color[0] + 30, 255), min(bg_color[1] + 30, 255), min(bg_color[2] + 30, 255))
        self.text_color = text_color
        self.rect = pg.Rect(pos[0], pos[1], size[0], size[1])
        self.is_hovered = False
    
    def draw(self, screen):
        color = self.hover_color if self.is_hovered else self.bg_color
        pg.draw.rect(screen, color, self.rect, border_radius=10)
        pg.draw.rect(screen, (50, 50, 50), self.rect, 3, border_radius=10)
        
        # Scale font size based on screen size
        font_size = int(32 * (HEIGHT / 960))
        font = pg.font.SysFont("Arial", font_size, True)
        text_surface = font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
    
    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
    
    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

def draw_menu(screen):
    """Draw the main menu screen"""
    screen.fill(pg.Color(40, 40, 40))
    
    title_font_size = int(80 * (HEIGHT / 960))
    title_font = pg.font.SysFont("Arial", title_font_size, True)
    title_text = title_font.render("CHESS GAME", True, pg.Color(255, 255, 255))
    title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 4))
    screen.blit(title_text, title_rect)
    
    subtitle_font_size = int(30 * (HEIGHT / 960))
    subtitle_font = pg.font.SysFont("Arial", subtitle_font_size)
    subtitle_text = subtitle_font.render("Select Game Mode", True, pg.Color(200, 200, 200))
    subtitle_rect = subtitle_text.get_rect(center=(WIDTH // 2, HEIGHT // 4 + int(80 * (HEIGHT / 960))))
    screen.blit(subtitle_text, subtitle_rect)

def show_menu(screen, clock):
    """Display menu and return selected game mode"""
    button_width = int(400 * (WIDTH / 960))
    button_height = int(70 * (HEIGHT / 960))
    button_x = (WIDTH - button_width) // 2
    spacing = int(85 * (HEIGHT / 960))
    start_y = HEIGHT // 2 - int(80 * (HEIGHT / 960))
    
    buttons = [
        Button("PLAY ONLINE (Network)", (button_x, start_y), (button_width, button_height), 
               (70, 130, 180), (255, 255, 255)),
        Button("LOCAL 2 PLAYER", (button_x, start_y + spacing), (button_width, button_height), 
               (138, 43, 226), (255, 255, 255)),
        Button("PLAY VS COMPUTER", (button_x, start_y + spacing * 2), (button_width, button_height), 
               (34, 139, 34), (255, 255, 255)),
        Button("COMPUTER VS COMPUTER", (button_x, start_y + spacing * 3), (button_width, button_height), 
               (178, 34, 34), (255, 255, 255))
    ]
    
    while True:
        mouse_pos = pg.mouse.get_pos()
        
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                exit()
            elif event.type == pg.MOUSEBUTTONDOWN:
                for i, button in enumerate(buttons):
                    if button.is_clicked(mouse_pos):
                        if i == 0:
                            return "network"
                        elif i == 1:
                            return "local"
                        elif i == 2:
                            return "vs_computer"
                        elif i == 3:
                            return "computer_vs_computer"
        
        for button in buttons:
            button.check_hover(mouse_pos)
        
        draw_menu(screen)
        for button in buttons:
            button.draw(screen)
        
        pg.display.flip()
        clock.tick(MAX_FPS)

def show_pause_menu(screen, clock, gs, valid_moves, square_selected):
    """Display pause menu overlay and return action"""
    button_width = int(350 * (WIDTH / 960))
    button_height = int(60 * (HEIGHT / 960))
    button_x = (WIDTH - button_width) // 2
    spacing = int(80 * (HEIGHT / 960))
    start_y = HEIGHT // 2 - int(80 * (HEIGHT / 960))
    
    buttons = [
        Button("RESUME", (button_x, start_y), (button_width, button_height), 
               (34, 139, 34), (255, 255, 255)),
        Button("RESTART", (button_x, start_y + spacing), (button_width, button_height), 
               (70, 130, 180), (255, 255, 255)),
        Button("QUIT TO MENU", (button_x, start_y + spacing * 2), (button_width, button_height), 
               (178, 34, 34), (255, 255, 255))
    ]
    
    while True:
        mouse_pos = pg.mouse.get_pos()
        
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                exit()
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_p:
                    return "resume"
            elif event.type == pg.MOUSEBUTTONDOWN:
                for i, button in enumerate(buttons):
                    if button.is_clicked(mouse_pos):
                        if i == 0:
                            return "resume"
                        elif i == 1:
                            return "restart"
                        elif i == 2:
                            return "quit"
        
        # Update button hover states
        for button in buttons:
            button.check_hover(mouse_pos)
        
        # Draw the game state in the background (dimmed)
        draw_game_state(screen, gs, valid_moves, square_selected)
        
        # Draw semi-transparent overlay
        overlay = pg.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        title_font_size = int(60 * (HEIGHT / 960))
        title_font = pg.font.SysFont("Arial", title_font_size, True)
        title_text = title_font.render("PAUSED", True, pg.Color(255, 255, 255))
        title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 4))
        screen.blit(title_text, title_rect)
        
        hint_font_size = int(20 * (HEIGHT / 960))
        hint_font = pg.font.SysFont("Arial", hint_font_size)
        hint_text = hint_font.render("Press P to resume", True, pg.Color(200, 200, 200))
        hint_rect = hint_text.get_rect(center=(WIDTH // 2, HEIGHT // 4 + int(60 * (HEIGHT / 960))))
        screen.blit(hint_text, hint_rect)
        
        for button in buttons:
            button.draw(screen)
        
        pg.display.flip()
        clock.tick(MAX_FPS)

def show_pause_menu_online(screen, clock, gs, valid_moves, square_selected, is_white_player):
    """Pause menu variant for online games (resume or quit)."""
    button_width = int(350 * (WIDTH / 960))
    button_height = int(60 * (HEIGHT / 960))
    button_x = (WIDTH - button_width) // 2
    spacing = int(80 * (HEIGHT / 960))
    start_y = HEIGHT // 2 - int(40 * (HEIGHT / 960))

    buttons = [
        Button("RESUME", (button_x, start_y), (button_width, button_height), (34, 139, 34), (255, 255, 255)),
        Button("QUIT TO MENU", (button_x, start_y + spacing), (button_width, button_height), (178, 34, 34), (255, 255, 255))
    ]

    while True:
        mouse_pos = pg.mouse.get_pos()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                exit()
            elif event.type == pg.KEYDOWN and event.key == pg.K_p:
                return "resume"
            elif event.type == pg.MOUSEBUTTONDOWN:
                for i, button in enumerate(buttons):
                    if button.is_clicked(mouse_pos):
                        return "resume" if i == 0 else "quit"

        for button in buttons:
            button.check_hover(mouse_pos)

        draw_game_state_online(screen, gs, valid_moves, square_selected, is_white_player)

        overlay = pg.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        title_font_size = int(60 * (HEIGHT / 960))
        title_font = pg.font.SysFont("Arial", title_font_size, True)
        title_text = title_font.render("PAUSED", True, pg.Color(255, 255, 255))
        title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 4))
        screen.blit(title_text, title_rect)

        hint_font_size = int(20 * (HEIGHT / 960))
        hint_font = pg.font.SysFont("Arial", hint_font_size)
        hint_text = hint_font.render("Press P to resume", True, pg.Color(200, 200, 200))
        hint_rect = hint_text.get_rect(center=(WIDTH // 2, HEIGHT // 4 + int(60 * (HEIGHT / 960))))
        screen.blit(hint_text, hint_rect)

        for button in buttons:
            button.draw(screen)

        pg.display.flip()
        clock.tick(MAX_FPS)

def show_pause_menu_online(screen, clock, gs, valid_moves, square_selected, is_white_player):
    """Pause overlay for online games (resume or quit)."""
    button_width = int(350 * (WIDTH / 960))
    button_height = int(60 * (HEIGHT / 960))
    button_x = (WIDTH - button_width) // 2
    spacing = int(80 * (HEIGHT / 960))
    start_y = HEIGHT // 2 - int(40 * (HEIGHT / 960))

    buttons = [
        Button("RESUME", (button_x, start_y), (button_width, button_height),
               (34, 139, 34), (255, 255, 255)),
        Button("QUIT TO MENU", (button_x, start_y + spacing), (button_width, button_height),
               (178, 34, 34), (255, 255, 255))
    ]

    while True:
        mouse_pos = pg.mouse.get_pos()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                exit()
            elif event.type == pg.KEYDOWN and event.key == pg.K_p:
                return "resume"
            elif event.type == pg.MOUSEBUTTONDOWN:
                for i, button in enumerate(buttons):
                    if button.is_clicked(mouse_pos):
                        return "resume" if i == 0 else "quit"

        for button in buttons:
            button.check_hover(mouse_pos)

        draw_game_state_online(screen, gs, valid_moves, square_selected, is_white_player)

        overlay = pg.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        title_font_size = int(60 * (HEIGHT / 960))
        title_font = pg.font.SysFont("Arial", title_font_size, True)
        title_text = title_font.render("PAUSED", True, pg.Color(255, 255, 255))
        title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 4))
        screen.blit(title_text, title_rect)

        hint_font_size = int(20 * (HEIGHT / 960))
        hint_font = pg.font.SysFont("Arial", hint_font_size)
        hint_text = hint_font.render("Press P to resume", True, pg.Color(200, 200, 200))
        hint_rect = hint_text.get_rect(center=(WIDTH // 2, HEIGHT // 4 + int(60 * (HEIGHT / 960))))
        screen.blit(hint_text, hint_rect)

        for button in buttons:
            button.draw(screen)

        pg.display.flip()
        clock.tick(MAX_FPS)

def draw_waiting_screen(screen, message):
    """Display waiting screen for network connection"""
    screen.fill(pg.Color(40, 40, 40))
    font_size = int(40 * (HEIGHT / 960))
    font = pg.font.SysFont("Arial", font_size, True)
    lines = message.split("\n")
    for idx, line in enumerate(lines):
        text = font.render(line, True, pg.Color(255, 255, 255))
        vertical_offset = (idx - (len(lines) - 1) / 2) * font_size * 1.2
        text_rect = text.get_rect(center=(WIDTH // 2, int(HEIGHT // 2 + vertical_offset)))
        screen.blit(text, text_rect)
    pg.display.flip()

def prompt_promotion_choice(screen, clock, piece_color, pawn_row, pawn_col, is_white_player=True):
    """Display compact UI next to the promoted pawn to select piece."""
    options = [('Q', 'Queen'), ('R', 'Rook'), ('B', 'Bishop'), ('N', 'Knight')]
    font_size = int(20 * (HEIGHT / 960))
    label_font = pg.font.SysFont("Arial", font_size)
    button_size = int(SQ_SIZE * 0.9)
    padding = int(SQ_SIZE * 0.15)
    
    if is_white_player:
        screen_col = pawn_col
        screen_row = pawn_row
    else:
        screen_col = 7 - pawn_col
        screen_row = 7 - pawn_row
    
    pawn_x = screen_col * SQ_SIZE
    pawn_y = screen_row * SQ_SIZE
    
    panel_width = button_size * 2 + padding * 3
    panel_height = button_size * 2 + padding * 3
    
    panel_x = pawn_x + SQ_SIZE + padding
    if panel_x + panel_width > WIDTH:
        panel_x = pawn_x - panel_width - padding
    
    panel_y = pawn_y - (panel_height - SQ_SIZE) // 2
    panel_y = max(padding, min(panel_y, HEIGHT - panel_height - padding))

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                exit()
            elif event.type == pg.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                for idx, (code, label) in enumerate(options):
                    row_idx = idx // 2
                    col_idx = idx % 2
                    rect = pg.Rect(
                        panel_x + padding + col_idx * (button_size + padding),
                        panel_y + padding + row_idx * (button_size + padding),
                        button_size, button_size
                    )
                    if rect.collidepoint(mouse_pos):
                        return code

        mouse_pos = pg.mouse.get_pos()
        
        panel_rect = pg.Rect(panel_x, panel_y, panel_width, panel_height)
        pg.draw.rect(screen, (40, 40, 40), panel_rect, border_radius=8)
        pg.draw.rect(screen, (200, 200, 200), panel_rect, 3, border_radius=8)
        
        for idx, (code, label) in enumerate(options):
            row_idx = idx // 2
            col_idx = idx % 2
            rect = pg.Rect(
                panel_x + padding + col_idx * (button_size + padding),
                panel_y + padding + row_idx * (button_size + padding),
                button_size, button_size
            )
            is_hover = rect.collidepoint(mouse_pos)
            bg_color = (70, 70, 70) if not is_hover else (110, 110, 110)
            pg.draw.rect(screen, bg_color, rect, border_radius=5)
            pg.draw.rect(screen, (180, 180, 180), rect, 2, border_radius=5)

            piece_code = piece_color + code
            piece_image = IMAGES.get(piece_code)
            if piece_image:
                scaled_image = pg.transform.scale(piece_image, (int(button_size * 0.7), int(button_size * 0.7)))
                img_rect = scaled_image.get_rect(center=rect.center)
                screen.blit(scaled_image, img_rect)

        pg.display.flip()
        clock.tick(MAX_FPS)

def play_online_game(screen, clock):
    """Handle online multiplayer game"""
    def wait_for_ack(message, close_connection=False):
        draw_waiting_screen(screen, message)
        waiting = True
        while waiting:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    exit()
                elif event.type in (pg.KEYDOWN, pg.MOUSEBUTTONDOWN):
                    waiting = False
            clock.tick(MAX_FPS)
        if close_connection and network is not None:
            network.close()

    draw_waiting_screen(screen, "Connecting to server...")
    network = None

    try:
        network = Network()
        player_color = network.connect()
    except NetworkError as exc:
        wait_for_ack(f"Connection failed: {exc}\nPress any key to return.")
        return
    
    draw_waiting_screen(screen, f"You are {player_color.upper()}! Waiting for opponent...")
    
    try:
        gs = network.send("get")
    except NetworkError as exc:
        wait_for_ack(f"Failed to get game state: {exc}\nPress any key to return.", close_connection=True)
        return
    if not gs:
        wait_for_ack("Failed to get game state! Press any key to return.", close_connection=True)
        return
    
    is_white_player = (player_color == "white")
    
    valid_moves = gs.get_valid_moves()
    animate = False
    move_made = False
    
    game_started = False
    start_sound_channel = None
    try:
        start_sound_channel = SOUNDS['game_start'].play()
    except:
        game_started = True
    
    running = True
    square_selected = ()
    player_clicks = []
    game_over = False
    
    while running:
        # Check if game start sound has finished
        if not game_started and start_sound_channel is not None:
            if not start_sound_channel.get_busy():
                game_started = True
        
        my_turn = (gs.white_to_move and is_white_player) or (not gs.white_to_move and not is_white_player)
        
        for e in pg.event.get():
            if e.type == pg.QUIT:
                running = False
                if network is not None:
                    network.close()
            elif e.type == pg.MOUSEBUTTONDOWN:
                if not game_over and my_turn and game_started:
                    location = pg.mouse.get_pos()
                    
                    if is_white_player:
                        col = location[0] // SQ_SIZE
                        rol = location[1] // SQ_SIZE
                    else:
                        col = 7 - (location[0] // SQ_SIZE)
                        rol = 7 - (location[1] // SQ_SIZE)
                    
                    if square_selected == (rol, col):
                        square_selected = ()
                        player_clicks = []
                    else:
                        square_selected = (rol, col)
                        player_clicks.append(square_selected)
                    
                    if len(player_clicks) == 2:
                        move = chessEngine.Move(player_clicks[0], player_clicks[1], gs.board)
                        print(move.get_chess_notation())
                        for i in range(len(valid_moves)):
                            if move == valid_moves[i]:
                                if valid_moves[i].is_pawn_promotion:
                                    choice = prompt_promotion_choice(screen, clock, valid_moves[i].piece_moved[0], 
                                                                    valid_moves[i].end_row, valid_moves[i].end_col, is_white_player)
                                    valid_moves[i].promotion_choice = choice
                                gs.make_move(valid_moves[i])
                                move_made = True
                                animate = True
                                try:
                                    gs = network.send(gs)
                                except NetworkError as exc:
                                    wait_for_ack(f"Disconnected: {exc}\nPress any key to return.", close_connection=True)
                                    return
                                square_selected = ()
                                player_clicks = []
                        if not move_made:
                            player_clicks = [square_selected]
            elif e.type == pg.KEYDOWN:
                if e.key == pg.K_ESCAPE:
                    running = False
                    if network is not None:
                        network.close()
                elif e.key == pg.K_p and not game_over:
                    pause_action = show_pause_menu_online(screen, clock, gs, valid_moves, square_selected, is_white_player)
                    if pause_action == "quit":
                        if network is not None:
                            network.close()
                        return
                elif e.key == pg.K_p and not game_over and game_started:
                    action = show_pause_menu_online(screen, clock, gs, valid_moves, square_selected, is_white_player)
                    if action == "quit":
                        if network is not None:
                            network.close()
                        return
                    else:
                        continue
        
        if not my_turn and not game_over:
            try:
                new_gs = network.send("get")
            except NetworkError as exc:
                wait_for_ack(f"Connection lost: {exc}\nPress any key to return.", close_connection=True)
                return
            if new_gs and len(new_gs.move_log) > len(gs.move_log):
                gs = new_gs
                move_made = True
                animate = True
        
        if move_made:
            if animate and gs.move_log:
                animation_move(gs.move_log[-1], screen, gs.board, clock, is_white_player)
            valid_moves = gs.get_valid_moves()
            if gs.move_log:
                is_check = gs.is_in_check
                play_move_sound(gs.move_log[-1], is_check)
            move_made = False
            animate = False
        
        draw_game_state_online(screen, gs, valid_moves, square_selected, is_white_player)
        
        if gs.check_mate or gs.stale_mate or gs.draw_by_repetition:
            if not game_over:
                game_over = True
                try:
                    SOUNDS['game_end'].play()
                except:
                    pass
                
                if gs.check_mate:
                    if gs.white_to_move:
                        result_message = "Black Wins!"
                    else:
                        result_message = "White Wins!"
                elif gs.stale_mate:
                    result_message = "Stalemate - Draw!"
                else:
                    result_message = "Draw by Repetition!"
                
                action = show_game_over_menu(screen, clock, gs, valid_moves, square_selected, result_message)
                if action == "rematch" or action == "quit":
                    if network is not None:
                        network.close()
                    return
        
        clock.tick(MAX_FPS)
        pg.display.flip()
    
    if network is not None:
        network.close()
        
def _player_flags_for_mode(game_mode):
    if game_mode == "local":
        return True, True
    if game_mode == "vs_computer":
        return True, False
    return False, False

def select_offline_mode(screen, clock):
    """Keep showing the menu until a non-network mode is selected."""
    while True:
        game_mode = show_menu(screen, clock)
        if game_mode == "network":
            play_online_game(screen, clock)
            continue
        player_one, player_two = _player_flags_for_mode(game_mode)
        return game_mode, player_one, player_two

def main():
    pg.init()
    pg.mixer.init()
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    clock = pg.time.Clock()
    load_images()
    load_sounds()
    game_mode, player_one, player_two = select_offline_mode(screen, clock)
    
    screen.fill(pg.Color("white"))
    gs = chessEngine.GameState()
    valid_moves = gs.get_valid_moves()
    animate = False
    move_made = False
    
    game_started = False
    start_sound_channel = None
    try:
        start_sound_channel = SOUNDS['game_start'].play()
    except:
        game_started = True
    
    running = True
    square_selected = ()
    player_clicks = []
    game_over = False
    while running:
        # Check if game start sound has finished
        if not game_started and start_sound_channel is not None:
            if not start_sound_channel.get_busy():
                game_started = True
        
        human_turn = (gs.white_to_move and player_one) or (not gs.white_to_move and player_two)
        for e in pg.event.get():
            if e.type == pg.QUIT:
                running = False
            elif e.type == pg.MOUSEBUTTONDOWN:
                if not game_over and human_turn and game_started:
                    location = pg.mouse.get_pos()
                    col = location[0] // SQ_SIZE
                    rol = location[1] // SQ_SIZE
                    if square_selected == (rol, col):
                        square_selected = ()
                        player_clicks = []
                    else:
                        square_selected = (rol, col)
                        player_clicks.append(square_selected)
                    if len(player_clicks) == 2:
                        move = chessEngine.Move(player_clicks[0], player_clicks[1], gs.board)
                        print(move.get_chess_notation())
                        for i in range(len(valid_moves)):
                            if move == valid_moves[i]:
                                if valid_moves[i].is_pawn_promotion:
                                    choice = prompt_promotion_choice(screen, clock, valid_moves[i].piece_moved[0], 
                                                                    valid_moves[i].end_row, valid_moves[i].end_col)
                                    valid_moves[i].promotion_choice = choice
                                gs.make_move(valid_moves[i])
                                move_made = True
                                animate = True
                                square_selected = ()
                                player_clicks = []
                        if not move_made:
                            player_clicks = [square_selected]
            elif e.type == pg.KEYDOWN:
                if e.key == pg.K_z:
                    gs.undo_move()
                    move_made = True
                    animate = False
                if e.key == pg.K_p:
                    pause_action = show_pause_menu(screen, clock, gs, valid_moves, square_selected)
                    if pause_action == "resume":
                        continue
                    elif pause_action == "restart":
                        # Restart with same game mode
                        gs = chessEngine.GameState()
                        valid_moves = gs.get_valid_moves()
                        square_selected = ()
                        player_clicks = []
                        move_made = False
                        animate = False
                        game_over = False
                        gs.check_mate = False
                        gs.stale_mate = False
                        gs.draw_by_repetition = False
                        game_started = False
                        try:
                            start_sound_channel = SOUNDS['game_start'].play()
                        except:
                            game_started = True
                    elif pause_action == "quit":
                        game_mode, player_one, player_two = select_offline_mode(screen, clock)
                        
                        gs = chessEngine.GameState()
                        valid_moves = gs.get_valid_moves()
                        square_selected = ()
                        player_clicks = []
                        move_made = False
                        animate = False
                        game_over = False
                        gs.check_mate = False
                        gs.stale_mate = False
                        gs.draw_by_repetition = False
                        game_started = False
                        try:
                            start_sound_channel = SOUNDS['game_start'].play()
                        except:
                            game_started = True
                if e.key == pg.K_r:
                    game_mode, player_one, player_two = select_offline_mode(screen, clock)
                    
                    gs = chessEngine.GameState()
                    valid_moves = gs.get_valid_moves()
                    square_selected = ()
                    player_clicks = []
                    move_made = False
                    animate = False
                    game_over = False
                    gs.check_mate = False
                    gs.stale_mate = False
                    gs.draw_by_repetition = False
                    game_started = False
                    try:
                        start_sound_channel = SOUNDS['game_start'].play()
                    except:
                        game_started = True

        if not game_over and not human_turn and game_started:
            ai_move = AI_move.find_best_move(gs, valid_moves)
            if ai_move is None:
                ai_move = AI_move.find_random_smart_move(valid_moves)
            gs.make_move(ai_move)
            move_made = True
            animate = True

        if move_made:
            if animate:
                animation_move(gs.move_log[-1], screen, gs.board, clock)
            valid_moves = gs.get_valid_moves()
            if gs.move_log:
                is_check = gs.is_in_check
                play_move_sound(gs.move_log[-1], is_check)
            move_made = False

        draw_game_state(screen, gs, valid_moves, square_selected)

        if gs.check_mate:
            game_over = True
            try:
                SOUNDS['game_end'].play()
            except:
                pass
            if gs.white_to_move:
                result_message = "Black Wins!"
            else:
                result_message = "White Wins!"
            
            action = show_game_over_menu(screen, clock, gs, valid_moves, square_selected, result_message)
            if action == "rematch":
                gs = chessEngine.GameState()
                valid_moves = gs.get_valid_moves()
                square_selected = ()
                player_clicks = []
                move_made = False
                animate = False
                game_over = False
                gs.check_mate = False
                gs.stale_mate = False
                game_started = False
                try:
                    start_sound_channel = SOUNDS['game_start'].play()
                except:
                    game_started = True
            elif action == "quit":
                # Return to main menu
                game_mode, player_one, player_two = select_offline_mode(screen, clock)
                
                gs = chessEngine.GameState()
                valid_moves = gs.get_valid_moves()
                square_selected = ()
                player_clicks = []
                move_made = False
                animate = False
                game_over = False
                gs.check_mate = False
                gs.stale_mate = False
                game_started = False
                try:
                    start_sound_channel = SOUNDS['game_start'].play()
                except:
                    game_started = True
        elif gs.stale_mate:
            game_over = True
            try:
                SOUNDS['game_end'].play()
            except:
                pass
            
            action = show_game_over_menu(screen, clock, gs, valid_moves, square_selected, "Stalemate - Draw!")
            if action == "rematch":
                gs = chessEngine.GameState()
                valid_moves = gs.get_valid_moves()
                square_selected = ()
                player_clicks = []
                move_made = False
                animate = False
                game_over = False
                gs.check_mate = False
                gs.stale_mate = False
                game_started = False
                try:
                    start_sound_channel = SOUNDS['game_start'].play()
                except:
                    game_started = True
            elif action == "quit":
                # Return to main menu
                game_mode, player_one, player_two = select_offline_mode(screen, clock)
                
                gs = chessEngine.GameState()
                valid_moves = gs.get_valid_moves()
                square_selected = ()
                player_clicks = []
                move_made = False
                animate = False
                game_over = False
                gs.check_mate = False
                gs.stale_mate = False
                game_started = False
                try:
                    start_sound_channel = SOUNDS['game_start'].play()
                except:
                    game_started = True
        elif gs.draw_by_repetition:
            game_over = True
            try:
                SOUNDS['game_end'].play()
            except:
                pass
            
            action = show_game_over_menu(screen, clock, gs, valid_moves, square_selected, "Draw by Repetition!")
            if action == "rematch":
                gs = chessEngine.GameState()
                valid_moves = gs.get_valid_moves()
                square_selected = ()
                player_clicks = []
                move_made = False
                animate = False
                game_over = False
                gs.check_mate = False
                gs.stale_mate = False
                game_started = False
                try:
                    start_sound_channel = SOUNDS['game_start'].play()
                except:
                    game_started = True
            elif action == "quit":
                # Return to main menu
                game_mode, player_one, player_two = select_offline_mode(screen, clock)
                
                gs = chessEngine.GameState()
                valid_moves = gs.get_valid_moves()
                square_selected = ()
                player_clicks = []
                move_made = False
                animate = False
                game_over = False
                gs.check_mate = False
                gs.stale_mate = False
                game_started = False
                try:
                    start_sound_channel = SOUNDS['game_start'].play()
                except:
                    game_started = True

        clock.tick(MAX_FPS)
        pg.display.flip()
        clock.tick(MAX_FPS)

def show_game_over_menu(screen, clock, gs, valid_moves, square_selected, message):
    """Display game over menu with result and options"""
    button_width = int(350 * (WIDTH / 960))
    button_height = int(60 * (HEIGHT / 960))
    button_x = (WIDTH - button_width) // 2
    spacing = int(80 * (HEIGHT / 960))
    start_y = HEIGHT // 2 + int(20 * (HEIGHT / 960))
    
    buttons = [
        Button("REMATCH", (button_x, start_y), (button_width, button_height), 
               (34, 139, 34), (255, 255, 255)),
        Button("QUIT TO MENU", (button_x, start_y + spacing), (button_width, button_height), 
               (178, 34, 34), (255, 255, 255))
    ]
    
    while True:
        mouse_pos = pg.mouse.get_pos()
        
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                exit()
            elif event.type == pg.MOUSEBUTTONDOWN:
                for i, button in enumerate(buttons):
                    if button.is_clicked(mouse_pos):
                        if i == 0:
                            return "rematch"
                        elif i == 1:
                            return "quit"
        
        # Update button hover states
        for button in buttons:
            button.check_hover(mouse_pos)
        
        # Draw the game state in the background (dimmed)
        draw_game_state(screen, gs, valid_moves, square_selected)
        
        # Draw semi-transparent overlay
        overlay = pg.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        title_font_size = int(60 * (HEIGHT / 960))
        title_font = pg.font.SysFont("Arial", title_font_size, True)
        title_text = title_font.render(message, True, pg.Color(255, 215, 0))
        title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
        screen.blit(title_text, title_rect)
        
        subtitle_font_size = int(28 * (HEIGHT / 960))
        subtitle_font = pg.font.SysFont("Arial", subtitle_font_size)
        subtitle_text = subtitle_font.render("Game Over", True, pg.Color(200, 200, 200))
        subtitle_rect = subtitle_text.get_rect(center=(WIDTH // 2, HEIGHT // 3 + int(70 * (HEIGHT / 960))))
        screen.blit(subtitle_text, subtitle_rect)
        
        for button in buttons:
            button.draw(screen)
        
        pg.display.flip()
        clock.tick(MAX_FPS)

def hight_light_squares(screen, gs, valid_moves, square_selected):
    if square_selected != ():
        r, c = square_selected
        if gs.board[r][c][0] == ('w' if gs.white_to_move else 'b'):
            s = pg.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100)
            s.fill(pg.Color('blue'))
            screen.blit(s, (c*SQ_SIZE, r*SQ_SIZE))
            s.fill(pg.Color('yellow'))
            for move in valid_moves:
                if move.start_row == r and move.start_col == c:
                    screen.blit(s, (move.end_col*SQ_SIZE, move.end_row*SQ_SIZE))


def draw_game_state(screen, gs, valid_moves, square_selected):
    draw_board(screen)
    hight_light_squares(screen, gs, valid_moves, square_selected)
    draw_pieces(screen, gs.board)

def draw_game_state_online(screen, gs, valid_moves, square_selected, is_white_player):
    """Draw game state with board flipped for black player"""
    draw_board_online(screen, is_white_player)
    hight_light_squares_online(screen, gs, valid_moves, square_selected, is_white_player)
    draw_pieces_online(screen, gs.board, is_white_player)

def draw_board(screen):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[((r + c) % 2)]
            pg.draw.rect(screen, color, pg.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))

def draw_board_online(screen, is_white_player):
    """Draw board flipped for black player"""
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[((r + c) % 2)]
            if is_white_player:
                pg.draw.rect(screen, color, pg.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
            else:
                pg.draw.rect(screen, color, pg.Rect((7-c)*SQ_SIZE, (7-r)*SQ_SIZE, SQ_SIZE, SQ_SIZE))
    

def draw_pieces(screen, board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":
                screen.blit(IMAGES[piece], pg.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))

def draw_pieces_online(screen, board, is_white_player):
    """Draw pieces with board flipped for black player"""
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":
                if is_white_player:
                    screen.blit(IMAGES[piece], pg.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
                else:
                    screen.blit(IMAGES[piece], pg.Rect((7-c)*SQ_SIZE, (7-r)*SQ_SIZE, SQ_SIZE, SQ_SIZE))

def hight_light_squares_online(screen, gs, valid_moves, square_selected, is_white_player):
    """Highlight squares with board flipped for black player"""
    if square_selected != ():
        r, c = square_selected
        if gs.board[r][c][0] == ('w' if gs.white_to_move else 'b'):
            s = pg.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100)
            s.fill(pg.Color('blue'))
            
            if is_white_player:
                screen.blit(s, (c*SQ_SIZE, r*SQ_SIZE))
            else:
                screen.blit(s, ((7-c)*SQ_SIZE, (7-r)*SQ_SIZE))
            
            s.fill(pg.Color('yellow'))
            for move in valid_moves:
                if move.start_row == r and move.start_col == c:
                    if is_white_player:
                        screen.blit(s, (move.end_col*SQ_SIZE, move.end_row*SQ_SIZE))
                    else:
                        screen.blit(s, ((7-move.end_col)*SQ_SIZE, (7-move.end_row)*SQ_SIZE))

def animation_move(move, screen, board, clock, is_white_player=True):
    global colors
    dR = move.end_row - move.start_row
    dC = move.end_col - move.start_col
    frames_per_square = 5
    frame_count = (abs(dR) + abs(dC)) * frames_per_square
    for frame in range(frame_count + 1):
        r, c = (move.start_row + dR * frame / frame_count, move.start_col + dC * frame / frame_count)
        
        if is_white_player:
            draw_board(screen)
        else:
            draw_board_online(screen, is_white_player)
        
        for row in range(DIMENSION):
            for col in range(DIMENSION):
                piece = board[row][col]
                if piece != "--":
                    if row == move.end_row and col == move.end_col:
                        continue
                    if is_white_player:
                        screen.blit(IMAGES[piece], pg.Rect(col*SQ_SIZE, row*SQ_SIZE, SQ_SIZE, SQ_SIZE))
                    else:
                        screen.blit(IMAGES[piece], pg.Rect((7-col)*SQ_SIZE, (7-row)*SQ_SIZE, SQ_SIZE, SQ_SIZE))
                
                if row == move.end_row and col == move.end_col and move.piece_captured != "--" and frame < frame_count:
                    if is_white_player:
                        screen.blit(IMAGES[move.piece_captured], pg.Rect(col*SQ_SIZE, row*SQ_SIZE, SQ_SIZE, SQ_SIZE))
                    else:
                        screen.blit(IMAGES[move.piece_captured], pg.Rect((7-col)*SQ_SIZE, (7-row)*SQ_SIZE, SQ_SIZE, SQ_SIZE))
        
        if is_white_player:
            screen.blit(IMAGES[move.piece_moved], pg.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
        else:
            screen.blit(IMAGES[move.piece_moved], pg.Rect((7-c)*SQ_SIZE, (7-r)*SQ_SIZE, SQ_SIZE, SQ_SIZE))
        
        pg.display.flip()
        clock.tick(60)

def draw_text(screen, text):
    font_size = int(50 * (HEIGHT / 960))
    font = pg.font.SysFont("Helvitca", font_size, True, False)
    text_object = font.render(text, 0, pg.Color('Grey'))
    text_location = pg.Rect(0, 0, WIDTH, HEIGHT).move(WIDTH/2 - text_object.get_width()/2, HEIGHT/2 - text_object.get_height()/2)
    screen.blit(text_object, text_location)
    text_object = font.render(text, 0, pg.Color('Black'))
    screen.blit(text_object, text_location.move(2, 2))

if __name__ == "__main__":
    main()