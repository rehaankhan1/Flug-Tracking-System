import pygame
import math
import requests

# Constants
WIDTH, HEIGHT = 800, 600
FPS = 60
RADIUS = 200  # Radius for the globe
CENTER_X, CENTER_Y = WIDTH // 2, HEIGHT // 2

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Revolving Earth Globe")
clock = pygame.time.Clock()

# Function to fetch flight data from a backend API
def fetch_flight_data():
    try:
        response = requests.get('http://localhost:5000/all-flights1')  # Adjust URL as necessary
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching flight data: {e}")
        return []

# Function to convert latitude and longitude to screen coordinates
def lat_lon_to_screen(lat, lon):
    """Convert latitude and longitude to screen coordinates for the globe."""
    x = CENTER_X + (RADIUS * math.cos(math.radians(lat)) * math.cos(math.radians(lon)))
    y = CENTER_Y + (RADIUS * math.sin(math.radians(lat)))
    return int(x), int(y)

# Main loop
running = True
angle = 0  # Angle for rotation

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Clear the screen
    screen.fill((0, 0, 0))  # Black background

    # Draw the globe as a circle
    pygame.draw.circle(screen, (0, 0, 255), (CENTER_X, CENTER_Y), RADIUS)  # Blue globe

    # Draw flight data markers
    flight_data = fetch_flight_data()
    for flight in flight_data:
        marker_x, marker_y = lat_lon_to_screen(flight['latitude'], flight['longitude'])
        pygame.draw.circle(screen, (255, 0, 0), (marker_x, marker_y), 5)  # Red markers for flights

    # Rotate the globe (angle changes over time)
    angle += 0.5  # Change this value for faster/slower rotation
    if angle >= 360:
        angle -= 360

    # Update the display
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
