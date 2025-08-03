"""
Detector de perros usando YOLOv8
Solo detecta perros con confianza >= 75%
"""

import cv2
import numpy as np
from ultralytics import YOLO
import logging

logger = logging.getLogger(__name__)

class YoloDogDetector:
    """
    Detector de perros usando YOLOv8 de Ultralytics
    """
    
    def __init__(self, confidence_threshold=0.60):
        """
        Inicializa el detector YOLO optimizado
        
        Args:
            confidence_threshold (float): Umbral mínimo de confianza (0.60 = 60%)
        """
        self.confidence_threshold = confidence_threshold
        self.dog_class_id = 16  # Clase "dog" en COCO dataset
        self.frame_skip = 2  # Procesar cada 2 frames para mejor rendimiento
        self.frame_count = 0
        self.last_detections = []  # Cache de últimas detecciones
        
        logger.info("🔄 Cargando modelo YOLOv8 optimizado...")
        try:
            # Carga YOLOv8 nano (más rápido que otros modelos)
            self.model = YOLO('yolov8n.pt')
            # Configurar para mejor rendimiento
            self.model.overrides['verbose'] = False
            logger.info("✅ YOLOv8 nano cargado exitosamente")
        except Exception as e:
            logger.error(f"❌ Error cargando YOLOv8: {e}")
            raise
    
    def detect_dogs(self, frame):
        """
        Detecta perros en el frame con optimización de rendimiento y cache
        
        Args:
            frame: Imagen de OpenCV (BGR)
            
        Returns:
            list: Lista de bounding boxes [(x, y, w, h), ...]
        """
        try:
            # Solo procesar cada N frames para mejorar rendimiento
            self.frame_count += 1
            if self.frame_count % self.frame_skip != 0:
                return self.last_detections  # Retornar detecciones anteriores
            
            # Procesar con tamaño reducido pero manteniendo calidad
            height, width = frame.shape[:2]
            scale_factor = 0.7  # Aumentar a 70% del tamaño original para mejor precisión
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            small_frame = cv2.resize(frame, (new_width, new_height))
            
            # Ejecutar detección en frame pequeño con parámetros optimizados
            results = self.model(small_frame, verbose=False, conf=self.confidence_threshold, iou=0.45)
            
            dog_boxes = []
            
            # Procesar resultados
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Obtener clase y confianza
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        
                        # Solo procesar si es un perro y supera el umbral
                        if class_id == self.dog_class_id and confidence >= self.confidence_threshold:
                            # Convertir coordenadas YOLO a formato OpenCV
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            
                            # Escalar coordenadas de vuelta al tamaño original
                            x1 = int(x1 / scale_factor)
                            y1 = int(y1 / scale_factor)
                            x2 = int(x2 / scale_factor)
                            y2 = int(y2 / scale_factor)
                            
                            x, y, w, h = x1, y1, x2 - x1, y2 - y1
                            
                            dog_boxes.append({
                                'bbox': (x, y, w, h),
                                'confidence': confidence
                            })
                            
                            logger.debug(f"🐕 Perro detectado: confianza {confidence:.2f}")
            
            # Actualizar cache
            self.last_detections = dog_boxes
            return dog_boxes
            
        except Exception as e:
            logger.error(f"Error en detección YOLO: {e}")
            return self.last_detections  # Retornar último estado conocido
    
    def draw_detections(self, frame, dog_detections):
        """
        Dibuja las detecciones en el frame
        
        Args:
            frame: Imagen de OpenCV
            dog_detections: Lista de detecciones de detect_dogs()
            
        Returns:
            frame: Imagen con detecciones dibujadas
        """
        for detection in dog_detections:
            bbox = detection['bbox']
            confidence = detection['confidence']
            
            x, y, w, h = bbox
            
            # Dibujar rectángulo verde para perros detectados
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Etiqueta con confianza
            label = f"DOG: {confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            
            # Fondo para el texto
            cv2.rectangle(frame, (x, y - label_size[1] - 10), 
                         (x + label_size[0], y), (0, 255, 0), -1)
            
            # Texto
            cv2.putText(frame, label, (x, y - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        return frame
    
    def get_best_dog_region(self, dog_detections):
        """
        Obtiene la región del perro con mayor confianza
        
        Args:
            dog_detections: Lista de detecciones
            
        Returns:
            tuple: (x, y, w, h) del perro con mayor confianza, o None
        """
        if not dog_detections:
            return None
        
        # Ordenar por confianza y tomar el mejor
        best_detection = max(dog_detections, key=lambda d: d['confidence'])
        return best_detection['bbox']
    
    def is_dog_detected(self, dog_detections):
        """
        Verifica si hay al menos un perro detectado
        
        Args:
            dog_detections: Lista de detecciones
            
        Returns:
            bool: True si hay perros detectados
        """
        return len(dog_detections) > 0
