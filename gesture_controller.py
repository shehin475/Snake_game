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
        self.mp_face = mp.solutions.face_detection
        
        # Initialize hands detection
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Initialize face detection
        self.face_detection = self.mp_face.FaceDetection(
            model_selection=0,
            min_detection_confidence=0.5
        )
        
        # Gesture state tracking
        self.previous_position = None
        self.position_smoothing = 0.5
        self.gesture_threshold = 0.04
        self.position_history = deque(maxlen=8)
        self.current_direction = None
        self.gesture_cooldown = 0
        self.max_cooldown = 5
        self.closed = False
        
    def detect_gestures(self, frame: np.ndarray) -> Tuple[Optional[str], bool, np.ndarray]:
        """
        Detect hand gestures and return direction and pinch state
        
        Args:
            frame: Input video frame
            
        Returns:
            Tuple of (direction, is_pinching, annotated_frame)
        """
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process hands
        hand_results = self.hands.process(rgb_frame)
        
        # Process face
        face_results = self.face_detection.process(rgb_frame)
        
        # Create annotated frame
        annotated_frame = frame.copy()
        
        direction = None
        is_pinching = False
        
        # Draw face detections
        if face_results.detections:
            for detection in face_results.detections:
                mp.solutions.drawing_utils.draw_detection(annotated_frame, detection)
        
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
                    self.position_history.clear()
                    self.position_history.append(current_pos.copy())
                else:
                    self.position_history.append(current_pos.copy())
                    if len(self.position_history) >= 4:
                        movement = self.position_history[-1] - self.position_history[0]

                        # Use net movement over several frames to reject landmark jitter.
                        if np.linalg.norm(movement) < self.gesture_threshold:
                            movement = None

                    else:
                        movement = None

                    if movement is not None:
                        if abs(movement[0]) > abs(movement[1]):
                            direction = "RIGHT" if movement[0] > 0 else "LEFT"
                        else:
                            direction = "DOWN" if movement[1] > 0 else "UP"

                        self.current_direction = direction
                        self.gesture_cooldown = self.max_cooldown
                        self.position_history.clear()
                        self.position_history.append(current_pos.copy())
                
                # Detect pinch gesture (thumb and index finger close)
                thumb_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
                index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
                
                thumb_pos = np.array([thumb_tip.x, thumb_tip.y])
                index_pos = np.array([index_tip.x, index_tip.y])
                
                distance = np.linalg.norm(thumb_pos - index_pos)
                is_pinching = distance < 0.05
                
                # Draw pinch indicator
                if is_pinching:
                    cv2.putText(annotated_frame, "SPEED BOOST!", (10, 30), 
                              cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                
                self.previous_position = current_pos
        else:
            self.reset_gesture_state()
        
        # Update cooldown
        if self.gesture_cooldown > 0:
            self.gesture_cooldown -= 1
        
        # Display current direction
        if self.current_direction:
            cv2.putText(annotated_frame, f"Direction: {self.current_direction}", 
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
        
        return direction, is_pinching, annotated_frame
    
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
        for resource in (self.hands, self.face_detection):
            try:
                resource.close()
            except Exception as error:
                close_errors.append(error)

        if close_errors:
            raise RuntimeError("Failed to close MediaPipe resources") from close_errors[0]