from PIL import Image

def show_image_in_terminal(path, width=60):
    img = Image.open(path).convert("RGB")
    w, h = img.size
    new_h = int(h * width / w / 2)
    img = img.resize((width, new_h))
    
    for y in range(new_h):
        line = ""
        for x in range(width):
            r, g, b = img.getpixel((x, y))
            line += f"\033[48;2;{r};{g};{b}m \033[0m"
        print(line)

# 调用：替换成你的图片路径
show_image_in_terminal("C:\\Users\\Admin\\Desktop\\kai后端\\用户照片\\WIN 60 HE512_9471d042-7bb6-4370-a238-8d7f4a960a55.webp")
print(r"你想发送的内容")
print(r"用户说明")
print(r"预定价格")