import os
import sys
import shutil
import random
from collections import defaultdict

# Định hình lại encoding cho console Windows để tránh lỗi ký tự Unicode tiếng Việt
sys.stdout.reconfigure(encoding='utf-8')

def split_dataset():
    # Đường dẫn thư mục gốc dataset mới
    base_dir = r"D:\KL_2025\new_dataset\detect_panadol_Redpolygon.v1i.yolov8-obb"
    train_dir = os.path.join(base_dir, "train")
    src_images_dir = os.path.join(train_dir, "images")
    src_labels_dir = os.path.join(train_dir, "labels")

    # Thư mục tạm để thực hiện chia
    temp_dir = os.path.join(base_dir, "temp_split")

    # 3 ảnh nền trống (Negative Samples) đã có sẵn trong train/images
    bg_image_names = [
        "Gemini_Generated_Image_7ckymw7ckymw7cky.png",
        "Gemini_Generated_Image_do9i5hdo9i5hdo9i.png",
        "Gemini_Generated_Image_t818at818at818at.png"
    ]

    print("=== BẮT ĐẦU PHÂN CHIA DATASET MỚI (GROUPED SPLIT) ===")

    # Bước 1: Kiểm tra thư mục nguồn
    if not os.path.exists(src_images_dir) or not os.path.exists(src_labels_dir):
        print("Lỗi: Không tìm thấy thư mục train/images hoặc train/labels!")
        return

    all_images = [f for f in os.listdir(src_images_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    all_labels = [f for f in os.listdir(src_labels_dir) if f.lower().endswith('.txt')]

    print(f"Tổng số ảnh trong train/images: {len(all_images)}")
    print(f"Tổng số nhãn trong train/labels: {len(all_labels)}")

    # Bước 2: Tách riêng 3 ảnh nền trống ra khỏi danh sách ảnh thường
    bg_images_found = [img for img in all_images if img in bg_image_names]
    regular_images  = [img for img in all_images if img not in bg_image_names]

    print(f"Số ảnh nền trống tìm thấy: {len(bg_images_found)}")
    print(f"Số ảnh có nhãn (để phân chia): {len(regular_images)}")

    # Bước 3: Gom nhóm ảnh thường theo tên ảnh gốc (trước '.rf.')
    groups = defaultdict(list)
    for img in regular_images:
        base_name, _ = os.path.splitext(img)
        if ".rf." in base_name:
            group_key = base_name.split(".rf.")[0]
        else:
            group_key = base_name
        groups[group_key].append(img)

    print(f"Số lượng nhóm ảnh gốc: {len(groups)}")

    # Bước 4: Phân chia nhóm theo tỉ lệ 80/10/10 với seed cố định
    group_keys = list(groups.keys())
    random.seed(42)
    random.shuffle(group_keys)

    total_groups = len(group_keys)
    val_size   = int(total_groups * 0.1)
    test_size  = int(total_groups * 0.1)
    train_size = total_groups - val_size - test_size

    train_groups = group_keys[:train_size]
    val_groups   = group_keys[train_size:train_size + val_size]
    test_groups  = group_keys[train_size + val_size:]

    print(f"Phân bổ nhóm: Train={len(train_groups)}, Val={len(val_groups)}, Test={len(test_groups)}")

    # Bước 5: Tạo các thư mục đích tạm thời
    subsets = ['train', 'valid', 'test']
    for subset in subsets:
        os.makedirs(os.path.join(temp_dir, subset, "images"), exist_ok=True)
        os.makedirs(os.path.join(temp_dir, subset, "labels"), exist_ok=True)

    # Hàm di chuyển file ảnh và nhãn theo danh sách nhóm
    def move_group_files(group_list, subset_name):
        img_count = 0
        lbl_count = 0
        for group in group_list:
            for img_file in groups[group]:
                base_name, _ = os.path.splitext(img_file)
                label_file = base_name + ".txt"

                src_img = os.path.join(src_images_dir, img_file)
                src_lbl = os.path.join(src_labels_dir, label_file)
                dst_img = os.path.join(temp_dir, subset_name, "images", img_file)
                dst_lbl = os.path.join(temp_dir, subset_name, "labels", label_file)

                if os.path.exists(src_img):
                    shutil.move(src_img, dst_img)
                    img_count += 1
                if os.path.exists(src_lbl):
                    shutil.move(src_lbl, dst_lbl)
                    lbl_count += 1
                else:
                    print(f"Cảnh báo: Không tìm thấy nhãn cho {img_file}")
        return img_count, lbl_count

    tr_img, tr_lbl   = move_group_files(train_groups, 'train')
    val_img, val_lbl = move_group_files(val_groups,   'valid')
    te_img, te_lbl   = move_group_files(test_groups,  'test')

    print(f"\n--- THỐNG KÊ SAU KHI CHIA DỮ LIỆU THƯỜNG ---")
    print(f"Train : {tr_img} ảnh, {tr_lbl} nhãn")
    print(f"Valid : {val_img} ảnh, {val_lbl} nhãn")
    print(f"Test  : {te_img} ảnh, {te_lbl} nhãn")

    # Bước 6: Di chuyển 3 ảnh nền trống vào temp_split/train (chúng đã có nhãn rỗng)
    print(f"\n--- XỬ LÝ ẢNH NỀN TRỐNG (NEGATIVE SAMPLES) ---")
    for bg_img in bg_images_found:
        base_name, _ = os.path.splitext(bg_img)
        bg_lbl       = base_name + ".txt"

        src_bg_img   = os.path.join(src_images_dir, bg_img)
        src_bg_lbl   = os.path.join(src_labels_dir, bg_lbl)
        dst_bg_img   = os.path.join(temp_dir, "train", "images", bg_img)
        dst_bg_lbl   = os.path.join(temp_dir, "train", "labels", bg_lbl)

        if os.path.exists(src_bg_img):
            shutil.move(src_bg_img, dst_bg_img)
            print(f"  + Đã chuyển ảnh nền: {bg_img}")
        else:
            print(f"  ! Không tìm thấy ảnh nền: {bg_img}")

        if os.path.exists(src_bg_lbl):
            shutil.move(src_bg_lbl, dst_bg_lbl)
            print(f"  + Đã chuyển nhãn nền: {bg_lbl}")
        else:
            # Tạo file nhãn rỗng nếu chưa có
            with open(dst_bg_lbl, 'w', encoding='utf-8') as f:
                pass
            print(f"  + Đã tạo nhãn rỗng mới: {bg_lbl}")

    # Bước 7: Xóa thư mục train cũ và sắp xếp lại cấu trúc
    try:
        shutil.rmtree(train_dir)
        print("\nĐã xóa thư mục train cũ.")
    except Exception as e:
        print(f"Lỗi khi xóa train cũ: {e}")

    try:
        for subset in subsets:
            src_subset = os.path.join(temp_dir, subset)
            dst_subset = os.path.join(base_dir, subset)
            shutil.move(src_subset, dst_subset)
        shutil.rmtree(temp_dir)
        print("Đã hoàn tất cấu trúc thư mục mới: train, valid, test.")
    except Exception as e:
        print(f"Lỗi khi sắp xếp thư mục: {e}")

    # Bước 8: Cập nhật file data.yaml
    yaml_path = os.path.join(base_dir, "data.yaml")
    yaml_content = "train: train/images\nval: valid/images\ntest: test/images\n\nnames:\n  0: Empty\n  1: Full\n  2: Partial\n"
    try:
        with open(yaml_path, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        print("Đã cập nhật file data.yaml thành công.")
    except Exception as e:
        print(f"Lỗi khi ghi data.yaml: {e}")

    # Bước 9: Thống kê kiểm tra cuối cùng
    print("\n=== THỐNG KÊ ĐỐI CHIẾU CUỐI CÙNG ===")
    for subset in ['train', 'valid', 'test']:
        sub_img_dir = os.path.join(base_dir, subset, "images")
        sub_lbl_dir = os.path.join(base_dir, subset, "labels")
        imgs = os.listdir(sub_img_dir) if os.path.exists(sub_img_dir) else []
        lbls = os.listdir(sub_lbl_dir) if os.path.exists(sub_lbl_dir) else []
        print(f"Thư mục '{subset}': {len(imgs)} ảnh, {len(lbls)} nhãn.")

if __name__ == "__main__":
    split_dataset()
