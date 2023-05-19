import os
from pprint import pprint

from PIL import Image, ImageDraw, ImageFont
from linebot import LineBotApi
from linebot.models import RichMenu, RichMenuSize, RichMenuArea, RichMenuBounds, URIAction, MessageAction

import settings



class Menu:
    """
    Menu object. Used for handle line's rich menu.
    """
    line_bot_api = LineBotApi(settings.line_token)

    def __init__(self, nrow: int, ncol: int, texts: list[str]):
        self.nrow = nrow
        self.ncol = ncol
        self.texts = texts
        self.row_size = 200
        self.col_size = 400
        self.color_bg = (255, 255, 255)
        self.color_fg = (0, 0, 0)
        self.font_path = self.downloadFont()
        self.img, self.rich_menu = self.draw()

    def downloadFont(self) -> str:
        """Download font and set font's path"""
        font_path = "NotoSerifCJK-Medium.ttc"
        if not os.path.exists(font_path):
            os.system(f"wget https://raw.githubusercontent.com/notofonts/noto-cjk/main/Serif/OTC/NotoSerifCJK-Medium.ttc -O {font_path}")
        return font_path

    def draw(self) -> None:
        """Draw texts on menu and save into PIL Image and menu object"""
        img  = Image.new(mode="RGBA", size=(self.ncol * self.col_size, self.nrow * self.row_size), color=self.color_bg)
        draw = ImageDraw.Draw(img)
        fnt = ImageFont.truetype(self.font_path, 40)
        buttons = []
        for i, text in enumerate(self.texts):
            x = (i %  self.ncol) * self.col_size
            y = (i // self.ncol) * self.row_size
            draw.multiline_text((x + self.col_size * 0.5, y + self.row_size * 0.5), text, font=fnt, anchor="mm", fill=self.color_fg)
            draw.rectangle([(x, y), (x + self.col_size, y + self.row_size)], outline=self.color_fg)
            buttons.append(
                RichMenuArea(
                    bounds=RichMenuBounds(x=x, y=y, width=self.col_size, height=self.row_size),
                    action=MessageAction(label=text, text=text),
                )
            )
        return img, RichMenu(
            size=RichMenuSize(width=img.width, height=img.height),
            selected=False,
            name="command_menu",
            chat_bar_text="命令選單",
            areas=buttons,
        )

    def show(self) -> None:
        """Show image. (Debug used)"""
        self.img.show()

    def save(self) -> None:
        """Save image"""
        self.img.save("menu.png", "PNG")

    def upload(self) -> None:
        """Create menu and upload menu image to LINE API"""
        self.save()
        self.rich_menu_id = self.line_bot_api.create_rich_menu(rich_menu=self.rich_menu)
        # self.rich_menu_id = "richmenu-febab324bfe02ca56e3bc82541193dd4"
        # return
        print(self.rich_menu_id)
        with open("menu.png", 'rb') as f:
            self.line_bot_api.set_rich_menu_image(self.rich_menu_id, "image/png", f)

    def setDeault(self) -> None:
        """Set menu to default menu"""
        self.line_bot_api.set_default_rich_menu(self.rich_menu_id)

    def linkUser(self, line_id: str) -> None:
        """Link menu to user"""
        self.line_bot_api.link_rich_menu_to_user(line_id, self.rich_menu_id)


def listAllMenu():
    line_bot_api = LineBotApi(settings.line_token)
    pprint(line_bot_api.get_rich_menu_list())
    print(line_bot_api.get_default_rich_menu())
    # linnil1
    # print(line_bot_api.get_rich_menu_id_of_user("Udb04a33910ef78f3b66da9da2cfeda89"))


def clearAllMenu():
    line_bot_api = LineBotApi(settings.line_token)
    for rich_menu in line_bot_api.get_rich_menu_list():
        # if rich_menu.rich_menu_id == "richmenu-febab324bfe02ca56e3bc82541193dd4":
        #     continue
        line_bot_api.delete_rich_menu(rich_menu.rich_menu_id)
    line_bot_api.unlink_rich_menu_from_user("Udb04a33910ef78f3b66da9da2cfeda89")


if __name__ == "__main__":
    clearAllMenu()
    menu = Menu(3, 3, [
        "加入團隊",
        "回報",
        "新增團隊",
        "列出團隊成員",
        "踢除隊員",
        "新增回報",
        "檢視回報",
        "結束回報",
    ])
    menu.save()
    menu.upload()
    menu.setDeault()
    # menu.linkUser("Udb04a33910ef78f3b66da9da2cfeda89")
