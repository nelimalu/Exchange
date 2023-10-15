import pygame
import time
pygame.font.init()

WIDTH = 1000
HEIGHT = 600
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cryptocurrency Exchange")

FONT = pygame.font.SysFont('consolas', 20, True)
LABEL_FONT = pygame.font.SysFont('consolas', 10, True)
TEXT_HEIGHT = FONT.render("TEST", 1, (255,255,255)).get_height() + 5  # extra 5 is padding
LABEL_TEXT_HEIGHT = LABEL_FONT.render("TEST", 1, (255,255,255)).get_height()
COLOUR = (255, 255, 255)
BACKGROUND = (0, 0, 0)
CHANGE_THRESHOLD = 0.2


def rangeMap(value, min1, max1, min2, max2):
    # min1, max1 is the value's current range, min2, max2 is the desired range
    range1 = float(max1) - float(min1)
    range2 = float(max2) - float(min2)
    scaled = (float(value) - float(min1)) / range1

    return scaled * range2 + float(min2)


def write(text, colour, location, font=FONT):
    text_rendered = font.render(text, 1, colour)
    win.blit(text_rendered, location)


def draw_lines(data):  # written for the identify slopes function
    for x, point in enumerate(data):
        if x == 0:
            pygame.draw.line(win, point[1], point[0], point[0])
        else:
            pygame.draw.line(win, point[1], point[0], data[x - 1][0])


def getGraphScale(data, height, font_height, scale_padding):
    labels = []

    minimum = min(data) - scale_padding
    maximum = max(data) + scale_padding
    amount_of_labels = height / (font_height * 2)
    scale = (maximum - minimum) / amount_of_labels

    for i in range(round(amount_of_labels)):
        labels.append(str(int(minimum + i * scale)))

    return labels


def identify_slope(data):
    slopes = []
    for x, pair in enumerate(data):
        if x == 0:
            slopes.append((pair, (255, 255, 255)))  # white means very little change
        prev = data[x - 1]

        try:
            slope = (pair[1] - prev[1]) / (pair[0] - prev[0])
        except ZeroDivisionError:
            slope = 0

        if CHANGE_THRESHOLD > slope > -CHANGE_THRESHOLD:
            slopes.append((pair, (255, 255, 255)))  # white means nothing changed
        if slope > CHANGE_THRESHOLD:
            slopes.append((pair, (255, 0, 0)))  # red means bad
        if slope < -CHANGE_THRESHOLD:
            slopes.append((pair, (0, 255, 0)))  # green means good

        slopes.append((pair, (255, 255, 255)))  # white means something went wrong

    return slopes


def get_change(value, past_value):
    if value == past_value[0]:
        return past_value[1]
    if value > past_value[0]:
        return "▲"
    if value < past_value[0]:
        return "▼"


class Graph:
    def __init__(self, x, y, width, height, history_length, scale_padding):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.thickness = 2
        self.history_length = history_length
        self.history_len_mins = history_length * 60
        self.padding = 5
        self.data = []
        self.timer = time.time()
        self.scale_padding = scale_padding
        self.first_update = True

        self.update_time = (history_length * 60 * 60) / width

    def update(self, live_data, title):
        if time.time() - self.timer >= self.update_time or self.first_update:
            self.first_update = False
            self.timer = time.time()
            if len(self.data) > self.width:
                self.data.pop()
            self.data.insert(0, live_data)

        scale = getGraphScale(self.data, self.height, LABEL_TEXT_HEIGHT, self.scale_padding)

        self.draw(scale, title)

    def draw(self, scale, title):
        title_pos = int(self.x + self.width / 2) - int(FONT.render(title, 1, (0,0,0)).get_width() / 2)
        write(title, COLOUR, (title_pos, self.y - TEXT_HEIGHT))

        write(str(self.history_len_mins) + " Minutes Ago", COLOUR, (self.x, self.y + self.height + self.padding), font=LABEL_FONT)
        write("Now", COLOUR, (self.x + self.width - LABEL_FONT.render("Now", 1, (0,0,0)).get_width(), self.y + self.height + self.padding), font=LABEL_FONT)

        for x, label in enumerate(scale):
            write(label, COLOUR,
                  (self.x - LABEL_FONT.render(label, 1, (0,0,0)).get_width() - self.padding,
                   (self.y + self.height) - (x * LABEL_TEXT_HEIGHT * 2) - 2 * LABEL_TEXT_HEIGHT),
                  font=LABEL_FONT)

        coord_data = []
        for x, i in enumerate(self.data):
            x = self.x + self.width - x
            y = rangeMap(i, scale[0], scale[-1], self.y + self.height, self.y)
            coord_data.append((x, y))

        slopes = identify_slope(coord_data)

        if len(self.data) > 1:
            draw_lines(slopes)

        pygame.draw.line(win, COLOUR, (self.x, self.y), (self.x, self.y + self.height), self.thickness)  # y axis
        pygame.draw.line(win, COLOUR, (self.x, self.y + self.height), (self.x + self.width, self.y + self.height), self.thickness)  # x axis


class UI:
    def __init__(self, crypto_sticker, base_sticker, start, history_length):
        self.crypto_sticker = crypto_sticker
        self.base_sticker = base_sticker
        self.start = start
        self.graph_history = 10  # 10 minutes

        self.price_graph = Graph(WIDTH / 2, 30, 400, 250, history_length, 30)
        self.theoretical_graph = Graph(WIDTH / 2, 330, 400, 250, history_length, 5)

        self.saved_price = [0, "▲"]
        self.saved_money = [0, "▲"]
        self.saved_crypto = [0, "▲"]
        self.saved_theoretical = [0, "▲"]
        self.saved_probability = [0, "▲"]

    def live_box(self, money, crypto, theoretical, price, decision, probability, padding_x, padding_y):
        price_change = get_change(price, self.saved_price)
        money_change = get_change(money, self.saved_money)
        crypto_change = get_change(crypto, self.saved_crypto)
        theoretical_change = get_change(theoretical, self.saved_theoretical)
        probability_change = get_change(probability, self.saved_probability)

        write('LIVE PRICE (' + self.crypto_sticker + ' to ' + self.base_sticker + "):", COLOUR, (padding_x, padding_y))
        write(str('{:.8f}'.format(price)) + " " + price_change, COLOUR, (padding_x, padding_y + TEXT_HEIGHT))

        write('LIVE BALANCE (' + self.base_sticker + "):", COLOUR, (padding_x, padding_y + TEXT_HEIGHT * 3))
        write(str('{:.8f}'.format(money)) + " " + money_change, COLOUR, (padding_x, padding_y + TEXT_HEIGHT * 4))

        write('LIVE CRYPTO (' + self.crypto_sticker + "):", COLOUR, (padding_x, padding_y + TEXT_HEIGHT * 6))
        write(str('{:.8f}'.format(crypto)) + " " + crypto_change, COLOUR, (padding_x, padding_y + TEXT_HEIGHT * 7))

        write('LIVE THEORETICAL BALANCE (' + self.base_sticker + "):", COLOUR, (padding_x, padding_y + TEXT_HEIGHT * 9))
        write(str('{:.8f}'.format(theoretical)) + " " + theoretical_change, COLOUR, (padding_x, padding_y + TEXT_HEIGHT * 10))

        write('LIVE BOT PROBABILITY:', COLOUR, (padding_x, padding_y + TEXT_HEIGHT * 12))
        write(str('{:.8f}'.format(probability)) + " " + probability_change, COLOUR, (padding_x, padding_y + TEXT_HEIGHT * 13))

        write('LIVE BOT DECISION:', COLOUR, (padding_x, padding_y + TEXT_HEIGHT * 15))
        write(decision, COLOUR, (padding_x, padding_y + TEXT_HEIGHT * 16))

        self.saved_price = [price, price_change] if self.saved_price != price else self.saved_price
        self.saved_money = [money, money_change] if self.saved_money != money else self.saved_money
        self.saved_crypto = [crypto, crypto_change] if self.saved_crypto != crypto else self.saved_crypto
        self.saved_theoretical = [theoretical, theoretical_change] if self.saved_theoretical != theoretical else self.saved_theoretical
        self.saved_probability = [probability, probability_change] if self.saved_probability != probability else self.saved_probability

    def update(self, money, crypto, theoretical, price, decision, probability):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        pos = pygame.mouse.get_pos()
        # print(pos)

        win.fill(BACKGROUND)

        self.live_box(money, crypto, theoretical, price, decision, probability, 20, 20)
        self.price_graph.update(price, "LIVE PRICE (" + self.crypto_sticker + " to " + self.base_sticker + ")")
        self.theoretical_graph.update(theoretical, "LIVE THEORETICAL BALANCE")

        pygame.display.flip()
