# ThalesDocsBot
A Chatbot to help you with Thales Products by providing info from Documentation   

   Built using [Streamlit](https://streamlit.io/), [Llama-Index](https://docs.llamaindex.ai/en/stable/), [Playwright](https://playwright.dev/) and [BeautifulSoup](https://beautiful-soup-4.readthedocs.io/en/latest/#:~:text=Beautiful%20Soup%20is%20a%20Python,hours%20or%20days%20of%20work.)


   
## Provides a helpful bot for Thales Products Documentation available over on www.thalesdocs.com
*NOTE:* Provide your OpenAI API Key on line 10   
Uses the latest GPT-4o Model   


  **Usage:**   
      1. Add your OpenAI API key on line# 10, if using hybrid or openAI bot   
      2. run `pip3 install -r ThalesDocsReq.txt` in terminal   
      3. Initialize Playwright by running `playwright install` in terminal   
      4. run `time python3 dataPrimer.py` in terminal   
      5. run `time python3 MarkdownIndexCreator.py` in Terminal   
      6. run `streamlit run {X}.py` in terminal (X = hybrid / OpenAI / Ollama)   

NOTE:    
   hybrid: hybridDocsGPT.py   
   OpenAI: ThalesDocsGPT.py   
   Ollama: MarkDownOllama_v3.py

