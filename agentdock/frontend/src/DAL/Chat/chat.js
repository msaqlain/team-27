export const DoChat = async function* (user_message, history) {
  try {
    let endpoint = "/api/chat";

    let formData = {
       "history": history,
      "question": user_message,
    };
    
    const base_url = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    const response = await fetch(base_url + endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(formData),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      yield decoder.decode(value, { stream: true }); 
    }
  } catch (error) {
    throw error;
  }
};
