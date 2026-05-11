class State:
    def __init__(self, engine):
        self.engine = engine
        
    def enter(self, **kwargs):
        pass
        
    def exit(self):
        pass
        
    def handle_events(self, events):
        pass
        
    def update(self, dt):
        pass
        
    def render(self, surface):
        pass


class StateMachine:
    def __init__(self, engine):
        self.engine = engine
        self.states = {}
        self.current_state = None
        
    def add_state(self, name, state_class):
        self.states[name] = state_class(self.engine)
        
    def change_state(self, name, **kwargs):
        if self.current_state:
            self.current_state.exit()
            
        self.current_state = self.states.get(name)
        if self.current_state:
            self.current_state.enter(**kwargs)
            
    def handle_events(self, events):
        if self.current_state:
            self.current_state.handle_events(events)
            
    def update(self, dt):
        if self.current_state:
            self.current_state.update(dt)
            
    def render(self, surface):
        if self.current_state:
            self.current_state.render(surface)
