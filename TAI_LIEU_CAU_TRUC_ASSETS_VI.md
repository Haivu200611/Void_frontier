# Tài Liệu Cấu Trúc Assets

Tài liệu này mô tả cấu trúc thư mục `assets/` cho dự án **Void Frontier**, theo hướng tách animation thành từng hành động và từng frame.

## 1. Cấu trúc thư mục `assets/`

```text
assets/
  images/
    sprites/
      players/
        idle/
          idle_01.png ... idle_08.png
        walk/
          walk_01.png ... walk_08.png
        run/
          run_01.png ... run_08.png
        jump/
          jump_01.png ... jump_04.png
        fall/
          fall_01.png ... fall_04.png
        attack/
          attack_01.png ... attack_06.png
        shoot/
          shoot_01.png ... shoot_06.png
        mining/
          mining_01.png ... mining_06.png
        hurt/
          hurt_01.png ... hurt_04.png
        death/
          death_01.png ... death_08.png

    enemies/
      alien/
        idle/
        move/
        attack/
        hurt/
        death/
      crystal_monster/
        idle/
        move/
        attack/
        hurt/
        death/
      parasite/
        idle/
        move/
        attack/
        hurt/
        death/
      robot/
        idle/
        move/
        attack/
        hurt/
        death/
      shadow/
        idle/
        move/
        attack/
        hurt/
        death/
      slime/
        idle/
        move/
        attack/
        hurt/
        death/
      void_creature/
        idle/
        move/
        attack/
        hurt/
        death/
      worm/
        idle/
        move/
        attack/
        hurt/
        death/

    bosses/
      mecha_beast/
        idle/
        move/
        charge/
        slam/
        laser/
        hurt/
        death/
      crystal_titan/
        idle/
        move/
        spikes/
        reflection/
        barrage/
        hurt/
        death/
      toxic_worm/
        idle/
        move/
        spit/
        burrow/
        hurt/
        death/
      void_guardian/
        idle/
        move/
        teleport/
        summon/
        blast/
        hurt/
        death/

    npc/
      trader/
        idle/
        talk/
      scientist/
        idle/
        talk/
      survivor/
        idle/
        talk/

    items/
      resources/
      consumables/
      artifacts/
      batteries/
      crafting/
      upgrades/
      quest/

    projectiles/
    weapons/
    spaceship/
    portraits/
    armor/   (tùy chọn; hiện tại repo đang có tên `amor/`)

  sounds/
    sfx/
      attack_melee.wav
      attack_heavy.wav
      attack_projectile.wav
      hit_normal.wav
      hit_heavy.wav
      hit_critical.wav
      hit_block.wav
      damage_taken.wav
      death_player.wav
      death_enemy.wav
      death_boss.wav
      boss_spawn.wav
      boss_attack.wav
      boss_phase.wav
      mine_hit.wav
    ui/
      pickup.wav
      button_click.wav
      button_hover.wav
      menu_open.wav
      menu_close.wav
      notification.wav
      levelup.wav
      equip.wav
    music/
      ambient_toxic.mp3
      ambient_crystal.mp3
      ambient_fungal.mp3
      ambient_void.mp3
      boss_battle.mp3
      menu_theme.mp3
    ambient/
      (tùy chọn, có thể thêm vòng lặp âm thanh môi trường sau)
```

## 2. Kích thước ảnh khuyến nghị theo từng loại

Nên dùng kích thước canvas đồng nhất theo từng nhóm để animation mượt, dễ căn tâm:

1. Player frames: `160x128`
2. Enemy frames: `96x96`
3. Boss frames: `256x256`
4. NPC frames: `96x128`
5. Projectile frames: `32x32` hoặc `64x32`
6. Item icons/sheets: `200x200`
7. Weapon icons: `32x32` hoặc `64x64`
8. Spaceship: `128x64`
9. Portraits: `512x1024` (hoặc tỉ lệ 1:2 nhất quán)

## 3. Quy ước đặt tên frame

Để dễ load tự động bằng code:

1. Dùng tên có số thứ tự: `action_01.png`, `action_02.png`, ...
2. Chữ thường toàn bộ, không dấu cách trong tên file/folder.
3. Mỗi action trong cùng một nhân vật nên có cùng kích thước canvas.
4. Giữ nhân vật ở cùng vị trí pivot (thường là giữa đáy) giữa các frame.

## 4. Ghi chú theo hiện trạng code

1. Hệ thống hiện tại đã có fallback khi thiếu ảnh/sound, nhưng để game “hoàn chỉnh” thì cần đủ assets.
2. Thư mục `assets/sounds/` hiện chưa có file thực tế, nên cần bổ sung để có âm thanh gameplay/UI/nhạc nền.
3. Một số sprite hiện tại trong repo có kích thước rất không đồng đều; nên chuẩn hóa dần theo nhóm ở mục 2.

