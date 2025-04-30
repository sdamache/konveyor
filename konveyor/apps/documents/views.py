from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods

from .services.document_adapter import DjangoDocumentService


def index(request: HttpRequest) -> HttpResponse:
    return HttpResponse("Documents app is working!")


@require_http_methods(["POST"])
def upload_document(request: HttpRequest) -> JsonResponse:
    try:
        file_obj = request.FILES["file"]
        document_service = DjangoDocumentService()
        doc = document_service.process_document(file_obj, file_obj.name)
        return JsonResponse(
            {"id": str(doc.id), "title": doc.title, "status": "success"}
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
