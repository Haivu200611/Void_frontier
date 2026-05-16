import pygame

from core.state_machine import State
from settings import *
from ui.background import SpaceBackground
from systems.localization import get_localization_manager


class HowToPlayState(State):
    def enter(self, **kwargs):
        self.font_page_title = pygame.font.SysFont("segoeui", 42, bold=True)
        self.font_heading = pygame.font.SysFont("segoeui", 26, bold=True)
        self.font_control = pygame.font.SysFont("segoeui", 20, bold=True)
        self.font_text = pygame.font.SysFont("segoeui", 19)
        self.font_small = pygame.font.SysFont("segoeui", 17)
        self.font_page_indicator = pygame.font.SysFont("segoeui", 18)

        self.loc_manager = get_localization_manager()
        self.background = SpaceBackground()
        self.current_page = 0
        self.pages = self.create_pages()
        self.transition_time = 0
        self.transition_duration = 0.3

    def create_pages(self):
        return self._create_pages_vi() if self.loc_manager.get_language() == "vi" else self._create_pages_en()

    def _create_pages_en(self):
        return [
            {
                "title": "HOW TO PLAY",
                "color": (50, 200, 200),
                "sections": [
                    {
                        "heading": "WELCOME TO VOID FRONTIER",
                        "content": [
                            "You are stranded on an alien planet at the edge of known space.",
                            "Your mission: SURVIVE, EXPLORE, and ESCAPE.",
                            "",
                            "- Mine resources from the alien terrain",
                            "- Craft and upgrade your equipment",
                            "- Battle dangerous enemies and bosses",
                            "- Collect artifacts to unlock your escape",
                        ],
                    }
                ],
            },
            {
                "title": "CONTROLS",
                "color": (255, 200, 100),
                "sections": [
                    {
                        "heading": "MOVEMENT & INTERACTION",
                        "controls": [
                            ("W / A / S / D", "Move"),
                            ("ARROW KEYS", "Alternative movement"),
                            ("SPACE", "Dodge roll"),
                            ("F", "Interact with NPCs / portals"),
                        ],
                    },
                    {
                        "heading": "MINING & COMBAT",
                        "controls": [
                            ("LEFT MOUSE", "Mine / Interact"),
                            ("RIGHT MOUSE", "Attack / Shoot"),
                            ("SCROLL WHEEL", "Switch tool or weapon"),
                        ],
                    },
                    {
                        "heading": "INVENTORY & MENU",
                        "controls": [
                            ("E", "Inventory"),
                            ("C", "Crafting"),
                            ("R", "Use item in active hotbar slot"),
                            ("ESC", "Back to Menu"),
                        ],
                    },
                ],
            },
            {
                "title": "SURVIVAL",
                "color": (255, 100, 150),
                "sections": [
                    {
                        "heading": "VITAL STATS",
                        "content": [
                            "Health: reaches 0 => Game Over.",
                            "Oxygen and Hunger matter in early chapters.",
                            "Collect drops and craft items to recover.",
                            "",
                            "Tip: keep moving and avoid long fights in hazard zones.",
                        ],
                    },
                    {
                        "heading": "CRAFTING & RESOURCES",
                        "content": [
                            "Mine ore nodes to gather materials.",
                            "Open crafting with C to build stronger tools.",
                            "Better gear helps you clear worlds faster.",
                        ],
                    },
                ],
            },
            {
                "title": "WORLDS & BOSSES",
                "color": (100, 200, 255),
                "sections": [
                    {
                        "heading": "WORLD PROGRESSION",
                        "content": [
                            "Chapter 1: Toxic Plains -> Mecha Beast",
                            "Chapter 2: Crystal Desert -> Crystal Titan",
                            "Chapter 3: Fungal Cave -> Toxic Worm",
                            "Chapter 4: Void Ruins -> Void Guardian",
                            "",
                            "Defeat bosses and collect artifacts to progress.",
                        ],
                    }
                ],
            },
            {
                "title": "NPC & TIPS",
                "color": (150, 255, 150),
                "sections": [
                    {
                        "heading": "NPC INTERACTION",
                        "content": [
                            "Press F near NPCs to interact and trade.",
                            "NPCs appear after boss progression.",
                            "",
                            "* Save before boss fights (F5).",
                            "* Load if needed (F9).",
                            "* Keep enough healing items in hotbar.",
                        ],
                    }
                ],
            },
        ]

    def _create_pages_vi(self):
        return [
            {
                "title": "HUONG DAN CHOI",
                "color": (50, 200, 200),
                "sections": [
                    {
                        "heading": "CHAO MUNG DEN VOID FRONTIER",
                        "content": [
                            "Ban bi mac ket tren hanh tinh la o ria vu tru.",
                            "Nhiem vu: SONG SOT, KHAM PHA va THOAT KHOI noi nay.",
                            "",
                            "- Khai thac tai nguyen tren dia hinh",
                            "- Che tao va nang cap trang bi",
                            "- Chien dau voi quai va boss",
                            "- Thu thap co vat de mo khoa duong thoat",
                        ],
                    }
                ],
            },
            {
                "title": "DIEU KHIEN",
                "color": (255, 200, 100),
                "sections": [
                    {
                        "heading": "DI CHUYEN & TUONG TAC",
                        "controls": [
                            ("W / A / S / D", "Di chuyen"),
                            ("PHIM MUI TEN", "Di chuyen thay the"),
                            ("SPACE", "Lan tranh"),
                            ("F", "Tuong tac NPC / cong dich chuyen"),
                        ],
                    },
                    {
                        "heading": "KHAI THAC & CHIEN DAU",
                        "controls": [
                            ("CHUOT TRAI", "Khai thac / Tuong tac"),
                            ("CHUOT PHAI", "Tan cong / Ban"),
                            ("LAN CHUOT", "Doi cong cu / vu khi"),
                        ],
                    },
                    {
                        "heading": "TUI DO & MENU",
                        "controls": [
                            ("E", "Mo / Dong tui do"),
                            ("C", "Mo che tao"),
                            ("R", "Dung vat pham o o hotbar dang chon"),
                            ("ESC", "Ve menu"),
                        ],
                    },
                ],
            },
            {
                "title": "SINH TON",
                "color": (255, 100, 150),
                "sections": [
                    {
                        "heading": "CHI SO QUAN TRONG",
                        "content": [
                            "Mau: ve 0 la thua cuoc.",
                            "Oxy va doi quan trong o cac chuong dau.",
                            "Nhat vat pham roi va che tao de hoi phuc.",
                            "",
                            "Meo: luon di chuyen, tranh danh lau trong vung nguy hiem.",
                        ],
                    },
                    {
                        "heading": "KHOANG SAN & CHE TAO",
                        "content": [
                            "Dao cac mo de lay nguyen lieu.",
                            "Nhan C de mo bang che tao cong cu manh hon.",
                            "Trang bi tot giup vuot map nhanh hon.",
                        ],
                    },
                ],
            },
            {
                "title": "WORLD & BOSS",
                "color": (100, 200, 255),
                "sections": [
                    {
                        "heading": "TIEN TRINH CAC CHUONG",
                        "content": [
                            "Chuong 1: Toxic Plains -> Mecha Beast",
                            "Chuong 2: Crystal Desert -> Crystal Titan",
                            "Chuong 3: Fungal Cave -> Toxic Worm",
                            "Chuong 4: Void Ruins -> Void Guardian",
                            "",
                            "Ha boss va thu thap co vat de mo khoa chuong tiep theo.",
                        ],
                    }
                ],
            },
            {
                "title": "NPC & MEO CHOI",
                "color": (150, 255, 150),
                "sections": [
                    {
                        "heading": "TUONG TAC NPC",
                        "content": [
                            "Nhan F khi dung gan NPC de trao doi / giao dich.",
                            "NPC xuat hien theo tien trinh ha boss.",
                            "",
                            "* Luu game truoc tran boss (F5).",
                            "* Tai game khi can (F9).",
                            "* Luon de san vat pham hoi mau trong hotbar.",
                        ],
                    }
                ],
            },
        ]

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.engine.state_machine.change_state("Menu")
                elif event.key in (pygame.K_RIGHT, pygame.K_DOWN):
                    if self.current_page < len(self.pages) - 1:
                        self.current_page += 1
                        self.transition_time = 0
                elif event.key in (pygame.K_LEFT, pygame.K_UP):
                    if self.current_page > 0:
                        self.current_page -= 1
                        self.transition_time = 0
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_x = event.pos[0]
                if mouse_x > WINDOW_WIDTH * 0.7:
                    if self.current_page < len(self.pages) - 1:
                        self.current_page += 1
                        self.transition_time = 0
                else:
                    if self.current_page > 0:
                        self.current_page -= 1
                        self.transition_time = 0

    def update(self, dt):
        self.background.update(dt)
        self.transition_time = min(self.transition_time + dt, self.transition_duration)

    def render(self, surface):
        self.background.render(surface)

        page = self.pages[self.current_page]

        panel = pygame.Surface((WINDOW_WIDTH - 40, WINDOW_HEIGHT - 60), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 200))
        pygame.draw.rect(surface, page["color"], (20, 20, WINDOW_WIDTH - 40, WINDOW_HEIGHT - 60), 3)
        pygame.draw.line(surface, page["color"], (20, 80), (WINDOW_WIDTH - 20, 80), 2)
        surface.blit(panel, (20, 20))

        title_surf = self.font_page_title.render(page["title"], True, page["color"])
        surface.blit(title_surf, (50, 35))

        y_pos = 110
        for section in page["sections"]:
            if "heading" in section:
                heading_surf = self.font_heading.render(section["heading"], True, (255, 255, 255))
                surface.blit(heading_surf, (60, y_pos))
                y_pos += 35

            if "controls" in section:
                for control_key, description in section["controls"]:
                    key_surf = self.font_control.render(control_key, True, (255, 200, 100))
                    surface.blit(key_surf, (80, y_pos))

                    desc_surf = self.font_text.render(description, True, (200, 200, 200))
                    surface.blit(desc_surf, (380, y_pos))
                    y_pos += 28
                y_pos += 15
            elif "content" in section:
                for line in section["content"]:
                    if line == "":
                        y_pos += 8
                    else:
                        is_bullet = line.startswith("-") or line.startswith("*")
                        color = (150, 255, 150) if is_bullet else (200, 200, 200)
                        line_surf = self.font_text.render(line, True, color)
                        surface.blit(line_surf, (80, y_pos))
                        y_pos += 26
                y_pos += 10

        is_vi = self.loc_manager.get_language() == "vi"
        bottom_y = WINDOW_HEIGHT - 35
        prev_text = "< TRANG TRUOC" if is_vi else "< PREVIOUS"
        next_text = "TRANG SAU >" if is_vi else "NEXT >"
        esc_text = "ESC de ve Menu" if is_vi else "ESC to Menu"
        page_label = "Trang" if is_vi else "Page"

        if self.current_page > 0:
            left_hint = self.font_small.render(prev_text, True, (100, 200, 255))
            surface.blit(left_hint, (40, bottom_y))

        page_text = self.font_page_indicator.render(
            f"{page_label} {self.current_page + 1} / {len(self.pages)}",
            True,
            (150, 150, 150),
        )
        page_rect = page_text.get_rect(center=(WINDOW_WIDTH // 2, bottom_y))
        surface.blit(page_text, page_rect)

        if self.current_page < len(self.pages) - 1:
            right_hint = self.font_small.render(next_text, True, (100, 200, 255))
            right_rect = right_hint.get_rect(right=WINDOW_WIDTH - 40)
            right_rect.y = bottom_y
            surface.blit(right_hint, right_rect)

        esc_hint = self.font_small.render(esc_text, True, (150, 100, 100))
        surface.blit(esc_hint, (WINDOW_WIDTH // 2 - esc_hint.get_width() // 2, WINDOW_HEIGHT - 15))
