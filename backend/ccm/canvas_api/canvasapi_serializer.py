from rest_framework import serializers

class CourseSerializer(serializers.Serializer):
    # Define the fields you want to update. Adjust fields according to the Canvas API.
    newNames = serializers.CharField(max_length=255, required=True)


class CourseSectionSerializer(serializers.Serializer):
    sections = serializers.ListField(
        child=serializers.CharField(max_length=255, required=True)
    )

    def validate_sections(self, value):
        if len(value) > 60:
            raise serializers.ValidationError("The list cannot be more than 60 items.")
        return value
