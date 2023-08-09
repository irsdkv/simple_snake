import random
import time
import toml
import dearpygui.dearpygui as dpg
from threading import Thread
from snake_util import *

settings_default = {"score_max": 0,
                    "speed": 5.5,
                    "speed_num": 12,
                    "snake_can_grow": True,
                    "through_walls": True,
                    "garden_size": 25}

SETTINGS_FILE_PATH = "./data/snake.toml"

with open(SETTINGS_FILE_PATH, 'r') as f:
    settings = toml.load(f)

    for def_key in settings_default.keys():
        if def_key not in settings.keys():
            settings = settings_default
            break


dpg_ids = {"score": 0,
           "score_max": 0,
           "speed": 0,
           "apple": 0,
           "save": 0,
           "garden_plot": 0}

score = 0
pause = False
TIME_DELAY_S = 0.8

user_datas = {"speed_up": "speed_up",
              "speed_down": "speed_down",
              "snake_growth": "snake_growth",
              "restart": "restart",
              "transparent_walls": "transparent_walls",
              "save": "save"}

body_rectangles: Dict[Position, int] = {}
colors = {"snake": [0, 255, 0], "apple": [255, 0, 0]}


direction_current = Direction.UP
directions_pressed_stack = []
apple_positions = []


def restart(snake_body_, __):
    global direction_current
    snake_body_.spawn()
    direction_current = Direction.UP
    update_max_score()
    update_score(0)
    draw_snake()


snake_body = SnakeBody(self_bite_callback_=restart, wall_bite_callback=restart,
                       transparent_walls=settings["through_walls"],
                       x_max=settings["garden_size"], y_max=settings["garden_size"])
snake_body.spawn()


dpg.create_context()
dpg.create_viewport(title='Simple Snake', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()


def pause_toggle():
    global pause
    pause = not pause


def update_score(score_new):
    global score, dpg_ids, settings
    score = score_new
    dpg.set_value(dpg_ids["score"], value=str(score))


def update_max_score():
    global direction_current, dpg_ids, score
    if score > settings["score_max"]:
        settings["score_max"] = score
        dpg.set_value(dpg_ids["score_max"], value=str(settings["score_max"]))


def speed_decrease():
    global settings, dpg_ids
    settings["speed"] -= (TIME_DELAY_S * 10 - 0.1 - settings["speed"]) / 3.
    settings["speed_num"] -= 1
    dpg.set_value(dpg_ids["speed"], value="x{}".format(settings["speed_num"]))


def speed_increase():
    global settings, dpg_ids
    if settings["speed"] < (TIME_DELAY_S * 10 - 0.1):
        settings["speed"] += (TIME_DELAY_S * 10 - 0.1 - settings["speed"]) / 3.
        settings["speed_num"] += 1
    dpg.set_value(dpg_ids["speed"], value="x{}".format(settings["speed_num"]))


def save():
    global settings, SETTINGS_FILE_PATH
    update_max_score()
    with open(SETTINGS_FILE_PATH, 'w') as f_:
        f_.write(toml.dumps(settings))


def callback(_, app_data, user_data):
    global user_datas, snake_body, settings
    if user_data == user_datas["speed_down"]:
        speed_decrease()
    elif user_data == user_datas["speed_up"]:
        speed_increase()
    elif user_data == user_datas["snake_growth"]:
        settings["snake_can_grow"] = app_data
    elif user_data == user_datas["restart"]:
        restart(snake_body, None)
    elif user_data == user_datas["transparent_walls"]:
        settings["through_walls"] = app_data
        snake_body.transparent_walls = settings["through_walls"]
    elif user_data == user_datas["save"]:
        save()


def draw_snake():
    global body_rectangles, dpg_ids, snake_body
    body_rectangles_c = copy.copy(body_rectangles)
    for pos, rectangle_id in body_rectangles_c.items():
        if pos not in snake_body.body:
            r_id = body_rectangles.pop(pos)
            dpg.delete_item(r_id)
    for pos in snake_body.body:
        if pos not in body_rectangles.keys():
            body_rectangles[pos] = dpg.draw_rectangle(pmin=[pos.x - 0.07, pos.y - 0.07],
                                                      pmax=[pos.x + 0.07, pos.y + 0.07],
                                                      color=colors["snake"], parent=dpg_ids["garden_plot"])


with dpg.window(label="Garden", pos=[0, 0], no_collapse=True, width=750, height=550, tag="Primary") \
        as main_window:

    with dpg.group(horizontal=True):
        with dpg.plot(no_menus=True, no_title=True, no_box_select=True, no_mouse_pos=False, no_highlight=True,
                      no_child=True,
                      width=500,
                      height=500,
                      equal_aspects=True) as snake_garden:
            dpg_ids["garden_plot"] = snake_garden
            default_x = dpg.add_plot_axis(axis=0, no_gridlines=True, no_tick_marks=True, no_tick_labels=True,
                                          label="", lock_min=True)
            dpg.set_axis_limits(axis=default_x, ymin=0, ymax=settings["garden_size"])
            default_y = dpg.add_plot_axis(axis=1, no_gridlines=True, no_tick_marks=True, no_tick_labels=True,
                                          label="", lock_min=True)
            dpg.set_axis_limits(axis=default_y, ymin=0, ymax=settings["garden_size"])

        with dpg.group():
            with dpg.group(horizontal=True):
                dpg.add_text("Score: ")
                dpg_ids["score"] = dpg.add_text("0")
                dpg.add_text("  Max score: ")
                dpg_ids["score_max"] = dpg.add_text(str(settings["score_max"]))

            dpg.add_separator()

            with dpg.group(horizontal=True):
                dpg.add_button(label="Speed Down", callback=callback, user_data=user_datas["speed_down"])
                speed_label_id = dpg.add_text("Speed: ")
                dpg_ids["speed"] = dpg.add_text("x{}".format(settings["speed_num"]))
                dpg.add_button(label="Speed Up", callback=callback, user_data=user_datas["speed_up"])

            dpg.add_separator()

            dpg.add_button(label="Restart", callback=callback, user_data=user_datas["restart"])

            dpg.add_separator()

            dpg.add_checkbox(label="Snake can grow", callback=callback, user_data=user_datas["snake_growth"],
                             default_value=settings["snake_can_grow"])

            dpg.add_checkbox(label="Through the walls", callback=callback, user_data=user_datas["transparent_walls"],
                             default_value=settings["through_walls"])

            dpg.add_separator()

            dpg.add_button(label="Save", callback=callback, user_data=user_datas["save"])


dpg.set_primary_window("Primary", True)


def key_release_handler(_, app_data):
    global directions_pressed_stack
    if app_data == dpg.mvKey_W or app_data == dpg.mvKey_Up:
        directions_pressed_stack.append(Direction.UP)
    elif app_data == dpg.mvKey_A or app_data == dpg.mvKey_Left:
        directions_pressed_stack.append(Direction.LEFT)
    elif app_data == dpg.mvKey_S or app_data == dpg.mvKey_Down:
        directions_pressed_stack.append(Direction.DOWN)
    elif app_data == dpg.mvKey_D or app_data == dpg.mvKey_Right:
        directions_pressed_stack.append(Direction.RIGHT)
    elif app_data == dpg.mvKey_Prior:
        speed_increase()
    elif app_data == dpg.mvKey_Next:
        speed_decrease()
    elif app_data == dpg.mvKey_Spacebar:
        pause_toggle()


with dpg.handler_registry(tag="keyboard_handler"):
    dpg.add_key_release_handler(callback=key_release_handler)


def spawn_apple():
    global apple_positions, dpg_ids
    apple_pos = Position(random.randint(0, 19), random.randint(0, 19))
    if dpg_ids["apple"] > 0:
        dpg.delete_item(dpg_ids["apple"])
    dpg_ids["apple"] = dpg.draw_rectangle(pmin=[apple_pos.x - 0.5, apple_pos.y - 0.5],
                                          pmax=[apple_pos.x + 1.5, apple_pos.y + 1.5],
                                          thickness=0, color=colors["apple"],
                                          fill=[255, 0, 0], parent=snake_garden)
    apple_positions = [apple_pos + Position(0, 0),
                       apple_pos + Position(0, 1),
                       apple_pos + Position(1, 0),
                       apple_pos + Position(1, 1)]

    for apple_bit in apple_positions:
        if apple_bit in snake_body.body:
            spawn_apple()


def apple_beaten():
    global score, settings
    if settings["snake_can_grow"]:
        snake_body.feed()
    spawn_apple()
    update_score(score + 1)


def upd():
    global directions_pressed_stack, TIME_DELAY_S, settings
    spawn_apple()
    while dpg.is_dearpygui_running():
        if pause:
            time.sleep(0.1)
            continue

        if directions_pressed_stack:
            snake_body.turn(directions_pressed_stack.pop(0))

        snake_body.move()
        if snake_body.head in apple_positions:
            apple_beaten()

        draw_snake()

        time.sleep(TIME_DELAY_S - settings["speed"] / 10)


thread = Thread(target=upd, args=())
thread.start()

while dpg.is_dearpygui_running():
    dpg.render_dearpygui_frame()

dpg.start_dearpygui()
dpg.destroy_context()
