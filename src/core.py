import pandas as pd
import numpy as np
import time
from .state import History, Fix8State
from . import mini_emtk

class Fix8Core:
    """
    Model class for Fix8.
    Stores and manages purely structural data (Pandas Dataframes, paths, states)
    and strictly non-GUI data operations previously built directly into Fix8.
    """
    def __init__(self):
        # fields relating to the stimulus
        self.image_file_path = None

        # fields relating to the trial folder
        self.folder_path = None
        self.trial_path = None
        self.trial_name = None

        # fields relating to fixations
        self.eye_events = None   # dataframe of eye events
        
        self.current_fixation = -1          # progress state
        self.suggested_corrections = None   # corrected fixations

        # field for tool undo/redo using memento pattern and state class
        self.state_history = History()

        # fields relating to AOIs
        self.aoi = None
        self.background_color = None

        # fields relating to the correction algorithm
        self.algorithm = "manual"
        self.algorithm_function = None
        self.secondary_algorithm_function = None
        self.suggested_fixation = None

        # keeps track of how many times file was saved so duplicates can be saved instead of overriding previous save file
        self.timer_start = 0  # beginning time of trial
        self.metadata = ""

        # fields relating to the drag and drop system
        self.selected_fixation = None           # clicked fixation
        self.xy = None
        self.locked_x = False    

        # fields relating to aoi margin
        self.aoi_width = 7
        self.aoi_height = 4

    def previous_fixation(self):
        """Moves the active fixation cursor backwards."""
        if self.current_fixation > 0:
            self.current_fixation -= 1

    def next_fixation(self):
        """Moves the active fixation cursor forwards."""
        if self.eye_events is None or self.eye_events.empty:
            return
            
        if self.current_fixation < len(self.eye_events) - 1:
            self.current_fixation += 1

    def update_fixation(self, index: int, new_x: float, new_y: float):
        """Manually corrects the position of a specific fixation."""
        if self.eye_events is None or self.eye_events.empty:
            return
            
        # Get the dataframe index for the Nth fixation
        fixations_only = self.eye_events[self.eye_events['eye_event'] == 'fixation']
        if index < 0 or index >= len(fixations_only):
            return
            
        real_df_index = fixations_only.index[index]
        
        # Overwrite coordinates
        self.eye_events.at[real_df_index, 'x_cord'] = new_x
        self.eye_events.at[real_df_index, 'y_cord'] = new_y

    def save_state(self):
        """Saves current state to history for undo functionality."""
        current_state = Fix8State(
            self.eye_events,
            self.suggested_corrections,
            self.current_fixation,
            self.selected_fixation,
        )
        self.state_history.set_state(current_state)

    def apply_noise(self, threshold):
        self.metadata += f"generate,noise {threshold},{time.time()}\n"
        self.save_state()

        self.eye_events["x_cord"] = self.eye_events["x_cord"] + np.random.normal(0, threshold, self.eye_events.shape[0])
        self.eye_events["y_cord"] = self.eye_events["y_cord"] + np.random.normal(0, threshold, self.eye_events.shape[0])

        if self.algorithm != "manual" and self.suggested_corrections is not None:
            self.suggested_corrections[:, 0] = self.eye_events["x_cord"]

    def apply_slope(self, threshold):
        self.metadata += f"generate,slope {threshold},{time.time()}\n"
        self.save_state()

        original_fixations = np.array(self.eye_events[['x_cord', 'y_cord', 'duration']])
        fixations = np.array(mini_emtk.error_droop(threshold, original_fixations))

        self.eye_events["x_cord"] = fixations[:, 0]
        self.eye_events["y_cord"] = fixations[:, 1]
        self.eye_events["duration"] = fixations[:, 2]

    def apply_offset(self, threshold):
        self.metadata += f"generate,offset {threshold},{time.time()}\n"
        self.save_state()

        original_fixations = np.array(self.eye_events[['x_cord', 'y_cord', 'duration']])
        fixations = np.array(mini_emtk.error_offset(threshold, original_fixations))
        
        self.eye_events["x_cord"] = fixations[:, 0]
        self.eye_events["y_cord"] = fixations[:, 1]
        self.eye_events["duration"] = fixations[:, 2]

    def apply_shift(self, threshold):
        self.metadata += f"generate,shift {threshold},{time.time()}\n"
        self.save_state()

        # get aoi from the image
        self.aoi, self.background_color = mini_emtk.EMTK_find_aoi(
            self.image_file_path,
            margin_height=self.aoi_height,
            margin_width=self.aoi_width,
        )

        # get line_Y from aoi
        line_Y = mini_emtk.find_lines_y(self.aoi)

        original_fixations = np.array(self.eye_events[['x_cord', 'y_cord', 'duration']])
        fixations = np.array(mini_emtk.error_shift(threshold, line_Y, original_fixations))
        self.eye_events["x_cord"] = fixations[:, 0]
        self.eye_events["y_cord"] = fixations[:, 1]
        self.eye_events["duration"] = fixations[:, 2]
