import pytest
from agents.motivational_agent import MotivationalAgent, MotivationRequest

def test_motivational_agent_initialization():
    """Test that the motivational agent initializes correctly"""
    agent = MotivationalAgent()
    assert agent is not None
    assert hasattr(agent, 'motivation_prompts')
    assert 'high_stress' in agent.motivation_prompts
    assert 'medium_stress' in agent.motivation_prompts
    assert 'low_stress' in agent.motivation_prompts

def test_generate_motivation_high_stress():
    """Test motivation generation for high stress level"""
    agent = MotivationalAgent()
    request = MotivationRequest(
        stress_level=8.5,
        recommended_activity="deep breathing exercises",
        user_message="I'm completely overwhelmed with work deadlines"
    )
    
    response = agent.generate_motivation(request)
    
    assert response.success is True
    assert len(response.motivational_message) > 0
    assert "breathing" in response.motivational_message.lower()

def test_generate_motivation_medium_stress():
    """Test motivation generation for medium stress level"""
    agent = MotivationalAgent()
    request = MotivationRequest(
        stress_level=5.0,
        recommended_activity="a short walk",
        user_message="I'm feeling a bit pressured with my tasks"
    )
    
    response = agent.generate_motivation(request)
    
    assert response.success is True
    assert len(response.motivational_message) > 0

def test_generate_motivation_low_stress():
    """Test motivation generation for low stress level"""
    agent = MotivationalAgent()
    request = MotivationRequest(
        stress_level=2.0,
        recommended_activity="stretching",
        user_message="I'm doing pretty well today"
    )
    
    response = agent.generate_motivation(request)
    
    assert response.success is True
    assert len(response.motivational_message) > 0

def test_generate_motivation_invalid_stress():
    """Test motivation generation with invalid stress level"""
    agent = MotivationalAgent()
    request = MotivationRequest(
        stress_level=15.0,  # Invalid value
        recommended_activity="meditation",
        user_message="I'm not feeling great"
    )
    
    response = agent.generate_motivation(request)
    
    # Should still return a message (fallback)
    assert len(response.motivational_message) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])