import graphene
import graphql_jwt

import howsmytrack.core.schema.mutation
import howsmytrack.core.schema.query


class Query(howsmytrack.core.schema.query.Query, graphene.ObjectType):
    pass


class Mutation(howsmytrack.core.schema.mutation.Mutation, graphene.ObjectType):
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
