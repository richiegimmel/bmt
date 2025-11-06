Project Name:  Board Management Tool
Company:  Atlas Machine and Supply, Inc.
Structure:  Atlas is a C Corporation incorporated in Kentucky
Ownership:  Atlas is owned by a single shareholder - the RICHARD F. GIMMEL III 2023 DECANTED GIFT TRUST.
Trustee:  The Trustee of the gift trust is Richard F Gimmel III

Project Scope:
This project encompassses building a full stack web application that will be used by the board members of Atlas Machine to manage the affairs of the board.  It's primary goal is to organize, track, and store documents.  It will also use an AI legal advisor via API connection to allow for the generation of new documents, and will include a chat interface to allow the users to ask questions in normal language and receive answers and legal advice.  The users should be able to generate a prompt and generate new documents via the chat.

Key Features:
- Ability to organize and store files, typically in the form of .docx, .pdf, and .xls
- AI chat interface with the ability to allow the user to ask questions and receive answers with citations from relevant documents or state laws.
- Ability to generate new documents via the chat interface.
- Ability to manage user logins with basic authorization.
- Limited RBAC - the only access controls needed are to allow for an admin role that has user management access.  All other users can access all features except for the user management function.

Example use case
Scenario:  Removing members from the board of directors.
User chat input:  "I am the majority shareholder, what is the proper process for removing members from the board?"
AI Action:  The AI reads the corporate governing documents to understand the proper process for board removal.  AI then uses web search and/or general to read the KY Statutes.  Once it has gathered this context and determined the proper answer to the user's question with a high level of confidence, it generates a response.
AI Output in chat:  The AI outputs the answer to the user's question in the chat.  Suppose in this scenario the AI determines it is necessary to have a resolution of the shareholders to remove the board members.  It would explain the process and cite the Atlas governing docs and/or external sources as required to substantiate its answer.  It would offer to generate the required resolution for the user.

Core Architecture
Frontend:  Next.js 
Backend:  FastAPI
Database:  PostgreSQL
Storage:  Local (ZFS)
CSS:  Tailwind v4 with ShadCN components and Lucide icons
Auth:  Open to ideas - keep simple but secure

AI Model Preference:
Since the AI chat tool will have agentic qualities, I would like to build this around Claude's new agent SDK.
Please reference the documentation on that here:  /home/richie/bmt/CLAUDE_AGENT_SDK.md
You can also use the Ref MCP server if needed to read the Claude Agent SDK documentation.

