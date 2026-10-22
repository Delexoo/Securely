from PIL import Image, ImageDraw

# Create a 64x64 icon with a shield design
size = 64
icon = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(icon)

# Draw shield shape (security symbol)
# Shield outline - main shape
shield_points = [
    (32, 8),   # Top center
    (52, 16),  # Top right
    (52, 40),  # Mid right
    (32, 56),  # Bottom center point
    (12, 40),  # Mid left
    (12, 16),  # Top left
]
draw.polygon(shield_points, fill='#58a6ff', outline='#1f6feb')

# Inner shield design - checkmark for "secure"
check_points = [
    (28, 32),  # Check pivot
    (30, 38),  # Check bottom
    (40, 24),  # Check top right
]
draw.line([(28, 32), (30, 38)], fill='white', width=4)
draw.line([(30, 38), (40, 24)], fill='white', width=4)

# Save as ICO file
icon.save('c:\\Users\\TeamB\\OneDrive\\Desktop\\Securely\\securely_icon.ico', format='ICO')
print("Icon created: securely_icon.ico")
