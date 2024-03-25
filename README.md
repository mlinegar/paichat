 This repository implements a chatbot that steps through a JSON script.
 
 Note: you will need to create a file called `api.env` in the working directory of the project that looks like:

```
openai-secret: sk-<your secret here>
openai-org: org-<your org here>
```

To run it, simply run: `python launch_chatserver.py`. It should also work in a docker container, though this may require some work and has not yet been tested. 
