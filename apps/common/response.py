from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomResponse:

    @staticmethod
    def _paginate_data(data, request, view, page_size: int = 10):

        """
        Helper method to paginate the provided queryset.
        """
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        paginated_data = paginator.paginate_queryset(data, request, view=view)

        pagination_details = {
            "count": paginator.page.paginator.count,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link()
        }
        return paginated_data, pagination_details

    @staticmethod
    def success(message: str, data=None, paginate: bool = False, request=None, view=None, page_size: int = 10, serializer_class=None, status_code: int = 200) -> Response:

        """
        Constructs a success response with optional pagination.
        Requires 'request' and 'view' if 'paginate' is True to enable pagination context.
        """

        response = {
            "status": "success",
            "message": message,
        }

        # Perform pagination if `paginate` is True and `request` and `view` are provided
        if paginate and data is not None:
            if request is None or view is None:
                raise ValueError("Request and view are required for pagination.")

            paginated_data, pagination_details = CustomResponse._paginate_data(data, request, view, page_size)
            response["pagination"] = pagination_details
            if serializer_class is not None:
                serializer = serializer_class(paginated_data, many=True, context={"request": request})
                response["data"] = serializer.data
            else:
                response["data"] = paginated_data
        elif data is not None:
            response["data"] = data

        return Response(response, status=status_code)

    @staticmethod
    def error(message: str, status_code: int=400) -> Response:

        response = {
            "status": "error",
            "message": message,
        }

        return Response(data=response, status=status_code)
