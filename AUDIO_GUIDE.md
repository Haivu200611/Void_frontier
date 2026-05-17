# 🎵 Hướng Dẫn Âm Thanh Void Frontier

## 📋 Tóm Tắt Các Âm Thanh Được Sử Dụng

### 🎼 Nhạc Nền (Music) - `assets/sounds/music/`

| Tên File | Vị Trí Sử Dụng | Mô Tả |
|----------|---|---|
| `game menu theme.mp3` | 📍 Menu chính | Nhạc menu chính của game |
| `toxic ambience.mp3` | 📍 Toxic Plains | Nhạc nền khu vực độc hại / phóng xạ |
| `crystal cave ambience.mp3` | 📍 Crystal Desert | Nhạc nền khu vực pha lê hoặc hang động phát sáng |
| `fungal ambience.mp3` | 📍 Fungal Cave | Nhạc nền khu vực nấm, đầm lầy hoặc sinh vật lạ |
| `void ambient.mp3` | 📍 Void Ruins | Nhạc nền khu vực void tối tăm, bí ẩn |
| `boss battle music.mp3` | 📍 Boss Fight | Nhạc chiến đấu boss |

### 🔊 Hiệu Ứng Âm Thanh (SFX) - `assets/sounds/sfx/`

#### ⚔️ Tấn Công (Combat Attacks)
| Tên File | Sử Dụng | Trạng Thái |
|----------|---------|------------|
| `attack_melee.wav` | Âm thanh bắn thường của súng nhỏ hoặc attack cơ bản | ✅ Đã áp dụng |
| `attack_heavy.wav` | Âm thanh bắn mạnh (damage ≥ 25) như shotgun, cannon | ✅ Đã áp dụng |
| `attack_projectile.wav` | Âm thanh bắn đạn năng lượng, laser, rocket hoặc plasma | ✅ Đã áp dụng |
| `boss_attack.wav` | Âm thanh boss dùng skill hoặc tấn công mạnh | ✅ Đã áp dụng |
| `mine_hit.wav` | Âm thanh đào quặng, đập đá hoặc đập kim loại | ✅ Đã áp dụng |

#### 💥 Đánh Trúng (Hit/Damage)
| Tên File | Sử Dụng | Trạng Thái |
|----------|---------|------------|
| `hit_normal.wav` | Âm thanh đạn trúng mục tiêu bình thường | ✅ Đã áp dụng |
| `hit_heavy.wav` | Âm thanh đạn mạnh va chạm gây lực lớn (damage ≥ 25) | ✅ Đã áp dụng |
| `hit_critical.wav` | Âm thanh chí mạng / headshot / critical hit | ✅ Đã áp dụng |
| `hit_block.wav` | Âm thanh đạn bị giáp hoặc khiên chặn lại | ⏳ Sẵn sàng (chờ block system) |
| `damage_taken.wav` | Âm thanh người chơi bị thương hoặc mất máu | ✅ Đã áp dụng |

#### ☠️ Sự Kiện Boss & Tử Vong
| Tên File | Sử Dụng | Trạng Thái |
|----------|---------|------------|
| `boss_spawn.wav` | Âm thanh boss xuất hiện hoặc bắt đầu trận đấu | ✅ Đã áp dụng |
| `boss_phase.wav` | Âm thanh boss chuyển phase / biến hình / nổi điên | ✅ Đã áp dụng |
| `death_boss.wav` | Âm thanh boss chết hoặc bị tiêu diệt | ✅ Đã áp dụng |
| `death_enemy.wav` | Âm thanh quái hoặc enemy chết | ✅ Đã áp dụng |
| `death_player.wav` | Âm thanh người chơi chết | ✅ Đã áp dụng |

### 🎮 Âm Thanh Giao Diện (UI) - `assets/sounds/ui/`

| Tên File | Sử Dụng | Trạng Thái |
|----------|---------|------------|
| `button_click.wav` | Âm thanh click nút giao diện | ✅ Đã áp dụng |
| `button_hover.wav` | Âm thanh rê chuột lên nút | ✅ Đã áp dụng |
| `menu_open.wav` | Âm thanh mở menu (Inventory/Crafting) | ✅ Đã áp dụng |
| `menu_close.wav` | Âm thanh đóng menu (Inventory/Crafting) | ✅ Đã áp dụng |
| `pickup.wav` | Âm thanh nhặt item hoặc loot | ✅ Đã áp dụng |
| `equip.wav` | Âm thanh trang bị item hoặc vũ khí | ✅ Đã áp dụng |
| `levelup.wav` | Âm thanh lên cấp / boss defeated reward | ✅ Đã áp dụng |
| `notification.wav` | Âm thanh thông báo quan trọng xuất hiện | ✅ Đã áp dụng |

---

## 🎯 Áp Dụng Chi Tiết

### ✅ Menu State (`states/menu_state.py`)
- Phát: `game menu theme.mp3` (fade in 1 giây)
- `button_hover.wav` khi rê chuột/phím lên nút
- `button_click.wav` khi chọn option

### ✅ Intro State (`states/intro_state.py`)
- Dừng nhạc menu khi video intro bắt đầu

### ✅ Play State (`states/play_state.py`)
- **Nhạc biome** dựa trên vị trí hiện tại (fade in 1 giây):
  - Toxic Plains → `toxic ambience.mp3`
  - Crystal Desert → `crystal cave ambience.mp3`
  - Fungal Cave → `fungal ambience.mp3`
  - Void Ruins → `void ambient.mp3`
- **Nhạc boss** → `boss battle music.mp3` tự động chuyển khi gặp boss
- **Khôi phục nhạc biome** khi boss chết
- **Boss SFX**:
  - `boss_spawn.wav` → khi boss xuất hiện
  - `boss_attack.wav` → khi boss chuyển state tấn công
  - `boss_phase.wav` → khi boss chuyển phase 2
  - `death_boss.wav` → khi boss chết
  - `levelup.wav` → fanfare khi boss bị tiêu diệt
- **Combat SFX**:
  - `attack_melee.wav` → melee attack
  - `attack_heavy.wav` → vũ khí damage ≥ 25
  - `attack_projectile.wav` → vũ khí damage < 25
  - `hit_normal.wav` → đạn trúng thường
  - `hit_heavy.wav` → đạn mạnh trúng (damage ≥ 25)
  - `hit_critical.wav` → chí mạng
  - `damage_taken.wav` → player bị thương
  - `death_enemy.wav` → quái chết
  - `death_player.wav` → player chết (+ game over)
- **Mining**:
  - `mine_hit.wav` → đào quặng thành công
- **UI SFX**:
  - `menu_open.wav` / `menu_close.wav` → mở/đóng inventory + crafting
  - `equip.wav` → trang bị vũ khí (phím G) + craft thành công
  - `pickup.wav` → nhặt item + dùng consumable
  - `notification.wav` → thông báo quan trọng (boss, upgrade, portal...)
- **Biome music transition** khi chuyển world qua portal

### ✅ Game Over State (`states/game_over_state.py`)
- Dừng nhạc hiện tại (fade out 0.5s)
- Phát `death_player.wav`
- `button_hover.wav` + `button_click.wav` cho navigation

---

## 📝 Cách Sử Dụng Audio Manager

### Phát Nhạc
```python
audio_manager = get_audio_manager()
audio_manager.play_music("game menu theme.mp3", fade_in=1.0)
```

### Dừng Nhạc
```python
audio_manager.stop_music(fade_out=0.5)
```

### Phát Hiệu Ứng Âm Thanh
```python
audio_manager.play_sfx("attack_melee.wav")
audio_manager.play_sfx("hit_critical.wav", volume=1.5)
```

### Phát Âm Thanh UI
```python
audio_manager.play_ui_sound("button_click.wav")
audio_manager.play_ui_sound("levelup.wav")
```

### UIAudioManager (tiện ích)
```python
from audio.ui_audio import UIAudioManager
ui_audio = UIAudioManager(audio_manager)
ui_audio.play_button_click()
ui_audio.play_menu_open()
ui_audio.play_notification()
ui_audio.play_equip()
ui_audio.play_pick_up()
ui_audio.play_level_up()
```

### CombatSoundManager (tiện ích)
```python
combat_sounds.play_attack_sound("melee")        # attack_melee.wav
combat_sounds.play_attack_sound("heavy")        # attack_heavy.wav
combat_sounds.play_attack_sound("projectile")   # attack_projectile.wav

combat_sounds.play_hit_sound("normal")          # hit_normal.wav
combat_sounds.play_hit_sound("heavy")           # hit_heavy.wav
combat_sounds.play_hit_sound("critical")        # hit_critical.wav
combat_sounds.play_hit_sound("block")           # hit_block.wav

combat_sounds.play_damage_sound()               # damage_taken.wav
combat_sounds.play_death_sound("player")        # death_player.wav
combat_sounds.play_death_sound("enemy")         # death_enemy.wav
combat_sounds.play_death_sound("boss")          # death_boss.wav
combat_sounds.play_boss_sound("spawn")          # boss_spawn.wav
combat_sounds.play_boss_sound("attack")         # boss_attack.wav
combat_sounds.play_boss_sound("phase")          # boss_phase.wav
```

### Điều Chỉnh Âm Lượng
```python
audio_manager.set_music_volume(0.7)      # 0.0 - 1.0
audio_manager.set_sfx_volume(0.8)        # 0.0 - 1.0
audio_manager.set_ambient_volume(0.5)    # 0.0 - 1.0
```

---

## 🔧 Để Phát Triển Thêm

### Có Thể Thêm:
- [ ] `hit_block.wav` → khi hệ thống block/giáp được triển khai
- [ ] Spatial audio (âm thanh theo khoảng cách)
- [ ] Ambient sound loops khi đang khai thác
- [ ] Dynamic music layers (intensity tăng theo combat)

---

**Cập nhật lần cuối:** 17/05/2026
**Trạng thái:** ✅ Hoàn chỉnh - 30/31 âm thanh đã được tích hợp
