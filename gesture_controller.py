"""
Gesture Recognition Module for Nokia Snake Game
Handles hand tracking and gesture detection using MediaPipe
"""

import cv2
import mediapipe as mp
import numpy as np
from collections import deque
from typing import Tuple, Optional

class GestureController:
    def __init__(self):
        """Initialize MediaPipe hands and gesture detection"""
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Initialize hands detection
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.4,
            min_tracking_confidence=0.4
        )
        
        # Gesture state tracking
        self.previous_position = None
        self.position_smoothing = 0.85
        self.movement_coherence = 0.7
        self.direction_dominance = 1.25
        self.gesture_windows = ((5, 0.07), (12, 0.06), (30, 0.055))
        self.position_history = deque(maxlen=40)
        self.current_direction = None
        self.gesture_cooldown = 0
        self.max_cooldown = 3
        self.closed = False
        
    def detect_gestures(self, frame: np.ndarray) -> Tuple[Optional[str], np.ndarray]:
        """
        Detect hand gestures and return the direction and annotated frame.
        
        Args:
            frame: Input video frame
            
        Returns:
            Tuple of (direction, annotated_frame)
        """
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process hands
        hand_results = self.hands.process(rgb_frame)
        
        # Create annotated frame
        annotated_frame = frame.copy()
        
        direction = None
        
        # Process hand landmarks
        if hand_results.multi_hand_landmarks:
            for hand_landmarks in hand_results.multi_hand_landmarks:
                # Draw hand landmarks
                self.mp_drawing.draw_landmarks(
                    annotated_frame, 
                    hand_landmarks, 
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                    self.mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2)
                )
                
                # Use the palm center to reduce errors from wrist movement and hand rotation.
                palm_landmarks = (
                    self.mp_hands.HandLandmark.WRIST,
                    self.mp_hands.HandLandmark.INDEX_FINGER_MCP,
                    self.mp_hands.HandLandmark.MIDDLE_FINGER_MCP,
                    self.mp_hands.HandLandmark.RING_FINGER_MCP,
                    self.mp_hands.HandLandmark.PINKY_MCP,
                )
                tracked_position = np.mean(
                    [
                        (
                            hand_landmarks.landmark[landmark].x,
                            hand_landmarks.landmark[landmark].y,
                        )
                        for landmark in palm_landmarks
                    ],
                    axis=0,
                )
                
                if self.previous_position is None:
                    current_pos = tracked_position
                else:
                    current_pos = (
                        self.previous_position
                        + self.position_smoothing
                        * (tracked_position - self.previous_position)
                    )

                if self.gesture_cooldown > 0:
                    self.gesture_cooldown -= 1

                self.position_history.append(current_pos.copy())
                for window_size, movement_threshold in self.gesture_windows:
                    if len(self.position_history) > window_size:
                        positions = list(self.position_history)[-window_size - 1:]
                        movement = positions[-1] - positions[0]
                        path_length = sum(
                            np.linalg.norm(current - previous)
                            for previous, current in zip(
                                positions, positions[1:]
                            )
                        )
                        coherence = (
                            np.linalg.norm(movement) / path_length
                            if path_length > 0
                            else 0.0
                        )

                        if (
                            np.linalg.norm(movement) < movement_threshold
                            or coherence < self.movement_coherence
                        ):
                            continue

                        horizontal = abs(movement[0])
                        vertical = abs(movement[1])
                        if horizontal >= vertical * self.direction_dominance:
                            direction = "RIGHT" if movement[0] > 0 else "LEFT"
                        elif vertical >= horizontal * self.direction_dominance:
                            direction = "DOWN" if movement[1] > 0 else "UP"

                        if direction is not None:
                            break

                if self.gesture_cooldown == 0 and direction is not None:
                    self.current_direction = direction
                    self.gesture_cooldown = self.max_cooldown
                    self.position_history.clear()
                    self.position_history.append(current_pos.copy())
                
                self.previous_position = current_pos
        else:
            self.reset_gesture_state()
            cv2.putText(
                annotated_frame,
                "NO HAND DETECTED",
                (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2,
            )
        
        # Display current direction
        if self.current_direction:
            cv2.putText(annotated_frame, f"Direction: {self.current_direction}", 
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
        
        return direction, annotated_frame
    
    def reset_gesture_state(self):
        """Reset gesture detection state"""
        self.previous_position = None
        self.position_history.clear()
        self.current_direction = None
        self.gesture_cooldown = 0

    def close(self):
        """Release MediaPipe resources."""
        if self.closed:
            return
        self.closed = True

        close_errors = []
        for resource in (self.hands,):
            try:
                resource.close()
            except Exception as error:
                close_errors.append(error)

        if close_errors:
            raise RuntimeError("Failed to close MediaPipe resources") from close_errors[0]