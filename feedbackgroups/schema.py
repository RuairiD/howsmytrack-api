import graphene
import graphql_jwt

import feedbackgroups.feedbackgroups.mutations
import feedbackgroups.feedbackgroups.schema


class Query(feedbackgroups.feedbackgroups.schema.Query, graphene.ObjectType):
    pass

class Mutation(feedbackgroups.feedbackgroups.schema.Mutation, graphene.ObjectType):
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
