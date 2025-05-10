from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import api_view
from .logic.chatbot_engine import ChatbotEngine
from django.conf import settings
import os
import logging


from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from .forms import RegisterForm


# Initialize logger
logger = logging.getLogger(__name__)

# Ensure media directory exists
os.makedirs(os.path.join(settings.BASE_DIR, 'media'), exist_ok=True)

# Initialize the chatbot engine
bot = ChatbotEngine()

def home(request):
    return render(request, 'base.html')

def chat_view(request):
    if request.method == "POST":
        question = request.POST.get("question", "").strip()
        document = request.FILES.get("document")
        response = ""

        if document:
            file_path = os.path.join(settings.BASE_DIR, 'media', document.name)

            try:
                # Save file temporarily
                with open(file_path, 'wb+') as destination:
                    for chunk in document.chunks():
                        destination.write(chunk)

                logger.info(f"File uploaded: {document.name} by {'anonymous' if not request.user.is_authenticated else request.user.username}")

                # Process file
                content_type = document.content_type.lower()
                if (document.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')) or content_type.startswith('image/')):
                    logger.info("Processing as image")
                    response = bot.process_image(file_path)
                else:
                    logger.info("Processing as document")
                    document_content = bot.process_document(file_path)
                    enhanced_question = f"{question}\n\nDocument content:\n{document_content}" if question else f"Please analyze this document:\n{document_content}"
                    response = bot.general_query(enhanced_question)

            except Exception as e:
                logger.error(f"Error processing file {document.name}: {str(e)}", exc_info=True)
                response = f"Error processing file: {str(e)}"

            finally:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        logger.debug(f"Temporary file removed: {file_path}")
                    except Exception as e:
                        logger.error(f"Error removing temp file: {str(e)}")

        elif question:
            logger.info(f"Processing text query: {question[:100]}...")
            response = bot.general_query(question)

        # Save chat history
        if question or document:
            try:
                bot.cursor.execute("INSERT INTO chat_history (user_query, bot_response) VALUES (?, ?)", (question, response))
                bot.conn.commit()
                logger.debug("Chat history updated")
            except Exception as e:
                logger.error(f"Error saving chat history: {str(e)}")

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"response": response})

        return render(request, 'base.html', {"response": response})

    return render(request, 'base.html')


class DocumentUploadView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        file = request.data.get("document")
        if not file:
            logger.warning("No file provided in DocumentUploadView")
            return Response({"error": "No file provided"}, status=400)

        file_path = os.path.join(settings.BASE_DIR, 'media', file.name)

        try:
            with open(file_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

            logger.info(f"API file upload: {file.name} by {'anonymous' if not request.user.is_authenticated else request.user.username}")

            content_type = file.content_type.lower()
            if (file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')) or content_type.startswith('image/')):
                result = bot.process_image(file_path)
            else:
                result = bot.process_document(file_path)

            return Response({"result": result})

        except Exception as e:
            logger.error(f"API error processing file {file.name}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=500)

        finally:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"API temp file removed: {file_path}")
                except Exception as e:
                    logger.error(f"Error removing API temp file: {str(e)}")


@api_view(['POST'])
def debug_upload(request):
    """Endpoint for testing file uploads"""
    file = request.FILES.get('document')
    if file:
        logger.info(f"Debug upload: {file.name} by {'anonymous' if not request.user.is_authenticated else request.user.username}")
        return Response({
            'name': file.name,
            'size': file.size,
            'content_type': file.content_type,
            'received': True
        })

    logger.warning("Debug upload called with no file")
    return Response({'error': 'No file received'}, status=400)




def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")  # Redirect to your main page
    else:
        form = RegisterForm()
    
    return render(request, "register.html", {"form": form})

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                if user.is_superuser:
                    return redirect("admin_dashboard")
                return redirect("home")
            else:
                messages.error(request, "Invalid username or password")
        else:
            messages.error(request, "Invalid username or password")
    
    form = AuthenticationForm()
    return render(request, "login.html", {"form": form})

def logout_view(request):
    logout(request)
    return redirect("login")


# # reg_f/views.py
def check_phishing_view(request):
    return render(request, "home.html")  # Create this template
