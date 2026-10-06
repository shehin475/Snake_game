import cv2
import pygame
import threading
import time
from gesture_controller import GestureController
from snake_game import SnakeGame

class GameManager:
    def __init__(self):
        """Initialize the game manager"""
        self.game = None
        self.gesture_controller = None
        self.cap = None
        self.running = True
        self.gesture_thread = None
        self.gesture_error = None
        self.cleaned_up = False
        self.gesture_state_lock = threading.Lock()
        
        # Gesture state
        self.current_gesture = None
        self.is_speed_boost = False
        
    def initialize_camera(self):
        """Initialize the webcam"""
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Could not open webcam")
            return False
        
        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        return True
    
    def gesture_detection_loop(self):
        """Main loop for gesture detection (runs in separate thread)"""
        try:
            while self.running and self.cap is not None:
                ret, frame = self.cap.read()
                if not ret:
                    if self.running:
                        time.sleep(0.033)
                    continue
                
                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)
                
                # Detect gestures
                gesture, pinch, annotated_frame = self.gesture_controller.detect_gestures(frame)
                
                # Update gesture state
                with self.gesture_state_lock:
                    if gesture is not None:
                        self.current_gesture = gesture
                    self.is_speed_boost = pinch
                
                # Display gesture window
                cv2.imshow('Nokia Snake - Gesture Control', annotated_frame)
                
                # Handle window close
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.running = False
                    break
                
                time.sleep(0.033)  # ~30 FPS
        except Exception as error:
            self.gesture_error = error
            self.running = False
    
    def run(self):
        """Main game loop"""
        try:
            self.game = SnakeGame()
            self.gesture_controller = GestureController()

            if not self.initialize_camera():
                print("Failed to initialize camera. Exiting...")
                return
            
            # Start gesture detection in separate thread
            self.gesture_thread = threading.Thread(target=self.gesture_detection_loop)
            self.gesture_thread.daemon = True
            self.gesture_thread.start()
            
            print("Nokia Snake Game Started!")
            print("Controls:")
            print("- Move your hand up/down/left/right to control the snake")
            print("- Pinch thumb and index finger for speed boost")
            print("- Swipe your hand upward when game over to restart")
            print("- Press ESC in game window to quit")
            print("\nGame Window: Classic Nokia Snake")
            print("Gesture Window: Webcam feed with hand tracking")
            
            # Main game loop
            last_update = time.time()
            
            while self.running:
                current_time = time.time()
                
                # Handle pygame events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.running = False
                
                # Apply gesture controls
                with self.gesture_state_lock:
                    gesture = self.current_gesture
                    self.current_gesture = None
                    speed_boost = self.is_speed_boost

                if gesture:
                    if self.game.game_over:
                        self.game.handle_restart(gesture)
                    else:
                        self.game.change_direction(gesture)
                
                # Apply speed boost
                self.game.set_speed_boost(speed_boost)
                
                # Update game at appropriate speed
                target_fps = self.game.get_current_speed()
                if current_time - last_update >= 1.0 / target_fps:
                    self.game.update()
                    last_update = current_time
                
                # Draw game
                self.game.draw()
                self.game.clock.tick(60)  # Display refresh rate

            if self.gesture_error is not None:
                raise RuntimeError("Gesture detection failed") from self.gesture_error
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        if self.cleaned_up:
            return
        self.cleaned_up = True

        print("Cleaning up...")
        self.running = False

        if self.gesture_thread and self.gesture_thread.is_alive():
            self.gesture_thread.join(timeout=1.0)

        cleanup_errors = []

        if self.cap is not None:
            try:
                self.cap.release()
            except Exception as error:
                cleanup_errors.append(error)
            finally:
                self.cap = None

        if self.gesture_thread and self.gesture_thread.is_alive():
            self.gesture_thread.join(timeout=2.0)

        if self.gesture_thread and self.gesture_thread.is_alive():
            cleanup_errors.append(
                RuntimeError("Gesture detection thread did not stop during cleanup")
            )
        elif self.gesture_controller is not None:
            try:
                self.gesture_controller.close()
            except Exception as error:
                cleanup_errors.append(error)

        try:
            cv2.destroyAllWindows()
        except Exception as error:
            cleanup_errors.append(error)

        if self.game is not None:
            try:
                self.game.quit()
            except Exception as error:
                cleanup_errors.append(error)

        if cleanup_errors:
            raise RuntimeError("One or more resources failed to close") from cleanup_errors[0]

        print("Game closed successfully!")

def main():
    """Main function"""
    try:
        game_manager = GameManager()
        game_manager.run()
    except KeyboardInterrupt:
        print("\nGame interrupted by user")
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
    