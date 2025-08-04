import { useState, useEffect } from 'react';

export type StepStatus = 'completed' | 'current' | 'locked';

export interface StepData {
  id: number;
  title: string;
  status: StepStatus;
  progress: number;
}

const INITIAL_STEPS: StepData[] = [
  { id: 1, title: "Market Research", status: "locked", progress: 0 },
  { id: 2, title: "Competitive Analysis", status: "locked", progress: 0 },
  { id: 3, title: "Target Audience Analysis", status: "locked", progress: 0 },
  { id: 4, title: "Value Proposition Design", status: "locked", progress: 0 },
  { id: 5, title: "Revenue Model Analysis", status: "locked", progress: 0 },
  { id: 6, title: "Risk Assessment", status: "locked", progress: 0 },
  { id: 7, title: "Marketing Strategy", status: "locked", progress: 0 },
  { id: 8, title: "Financial Projections", status: "locked", progress: 0 },
  { id: 9, title: "Implementation Plan", status: "locked", progress: 0 },
];

export function useStepProgress() {
  const [steps, setSteps] = useState<StepData[]>(INITIAL_STEPS);
  const [isValidated, setIsValidated] = useState(false);

  useEffect(() => {
    // Load validation status from sessionStorage
    if (typeof window !== 'undefined') {
      const validated = sessionStorage.getItem('brandorb_validated') === 'true';
      setIsValidated(validated);
      
      if (validated) {
        // Load step progress from localStorage
        const savedSteps = localStorage.getItem('brandorb_step_progress');
        if (savedSteps) {
          try {
            setSteps(JSON.parse(savedSteps));
          } catch {
            updateStepsAfterValidation();
          }
        } else {
          updateStepsAfterValidation();
        }
      }
    }
  }, []);

  const updateStepsAfterValidation = () => {
    const updatedSteps = INITIAL_STEPS.map((step, index) => {
      if (index <= 7) { // Steps 1-8 completed after validation
        return { ...step, status: 'completed' as StepStatus, progress: 100 };
      } else if (index === 8) { // Step 9 becomes current
        return { ...step, status: 'current' as StepStatus, progress: 0 };
      }
      return step;
    });
    
    setSteps(updatedSteps);
    localStorage.setItem('brandorb_step_progress', JSON.stringify(updatedSteps));
  };

  const markStepCompleted = (stepId: number) => {
    const updatedSteps = steps.map(step => {
      if (step.id === stepId) {
        return { ...step, status: 'completed' as StepStatus, progress: 100 };
      } else if (step.id === stepId + 1) {
        return { ...step, status: 'current' as StepStatus };
      }
      return step;
    });
    
    setSteps(updatedSteps);
    localStorage.setItem('brandorb_step_progress', JSON.stringify(updatedSteps));
  };

  return {
    steps,
    isValidated,
    markStepCompleted,
    updateStepsAfterValidation,
  };
}
